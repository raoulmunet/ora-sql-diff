from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from ora_core import analyze_sql, normalize_identifier


@dataclass(frozen=True)
class Change:
    kind: str
    detail: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class DiffResult:
    changes: list[Change]

    @property
    def changed(self) -> bool:
        return bool(self.changes)

    def to_dict(self) -> dict:
        return {"changed": self.changed, "changes": [c.to_dict() for c in self.changes]}


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"--[^\n]*", " ", text)
    return text


def _split_top_level_csv(text: str) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    depth = 0
    in_string = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "'":
            if in_string and i + 1 < len(text) and text[i + 1] == "'":
                buf.extend(("'", "'"))
                i += 2
                continue
            in_string = not in_string
            buf.append(ch)
        elif not in_string and ch == "(":
            depth += 1
            buf.append(ch)
        elif not in_string and ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif not in_string and depth == 0 and ch == ",":
            item = _collapse_ws("".join(buf))
            if item:
                out.append(item)
            buf = []
        else:
            buf.append(ch)
        i += 1
    item = _collapse_ws("".join(buf))
    if item:
        out.append(item)
    return out


def _projection(sql: str) -> list[str]:
    m = re.search(r"\bSELECT\b(.*?)\bFROM\b", sql, re.I | re.S)
    if not m:
        return []
    items = []
    for expr in _split_top_level_csv(m.group(1)):
        expr = re.sub(r"\s+AS\s+[A-Za-z][\w$#]*\s*$", "", expr, flags=re.I)
        expr = re.sub(r"\s+[A-Za-z][\w$#]*\s*$", "", expr) if "." in expr else expr
        items.append(_collapse_ws(expr).upper())
    return items


def _join_map(sql: str) -> dict[str, str]:
    out: dict[str, str] = {}
    pattern = re.compile(
        r"\b(?:(INNER|LEFT|RIGHT|FULL|CROSS)\s+)?JOIN\s+"
        r"([A-Za-z][\w$#]*(?:\.[A-Za-z][\w$#]*)?)",
        re.I,
    )
    for m in pattern.finditer(sql):
        join_type = (m.group(1) or "INNER").upper()
        out[normalize_identifier(m.group(2))] = join_type
    return out


def _clause(sql: str, keyword: str, stop_keywords: tuple[str, ...]) -> str | None:
    stops = "|".join(re.escape(x) for x in stop_keywords)
    pattern = rf"\b{re.escape(keyword)}\b(.*?)(?=\b(?:{stops})\b|$)"
    m = re.search(pattern, sql, re.I | re.S)
    return _collapse_ws(m.group(1)).upper() if m else None


def compare_sql(before: str, after: str) -> DiffResult:
    before_clean = _collapse_ws(_strip_comments(before))
    after_clean = _collapse_ws(_strip_comments(after))

    changes: list[Change] = []

    b_analysis = analyze_sql(before_clean)
    a_analysis = analyze_sql(after_clean)

    for obj in sorted(set(a_analysis.all_objects) - set(b_analysis.all_objects)):
        changes.append(Change("OBJECT_ADDED", obj))
    for obj in sorted(set(b_analysis.all_objects) - set(a_analysis.all_objects)):
        changes.append(Change("OBJECT_REMOVED", obj))

    b_proj = set(_projection(before_clean))
    a_proj = set(_projection(after_clean))
    for item in sorted(a_proj - b_proj):
        changes.append(Change("PROJECTION_ADDED", item))
    for item in sorted(b_proj - a_proj):
        changes.append(Change("PROJECTION_REMOVED", item))

    b_joins = _join_map(before_clean)
    a_joins = _join_map(after_clean)
    for obj in sorted(set(b_joins) & set(a_joins)):
        if b_joins[obj] != a_joins[obj]:
            changes.append(Change("JOIN_TYPE_CHANGED", f"{obj} {b_joins[obj]} -> {a_joins[obj]}"))

    for obj in sorted(set(a_joins) - set(b_joins)):
        changes.append(Change("JOIN_ADDED", f"{obj} ({a_joins[obj]})"))
    for obj in sorted(set(b_joins) - set(a_joins)):
        changes.append(Change("JOIN_REMOVED", f"{obj} ({b_joins[obj]})"))

    clause_specs = [
        ("WHERE", ("GROUP BY", "HAVING", "ORDER BY", "FETCH", "OFFSET", "UNION", "INTERSECT", "MINUS")),
        ("GROUP BY", ("HAVING", "ORDER BY", "FETCH", "OFFSET", "UNION", "INTERSECT", "MINUS")),
        ("HAVING", ("ORDER BY", "FETCH", "OFFSET", "UNION", "INTERSECT", "MINUS")),
        ("ORDER BY", ("FETCH", "OFFSET", "UNION", "INTERSECT", "MINUS")),
    ]

    for label, stops in clause_specs:
        b = _clause(before_clean, label, stops)
        a = _clause(after_clean, label, stops)
        if b != a:
            if b is None and a is not None:
                changes.append(Change(label.replace(" ", "_") + "_ADDED", a))
            elif b is not None and a is None:
                changes.append(Change(label.replace(" ", "_") + "_REMOVED", b))
            else:
                changes.append(Change(label.replace(" ", "_") + "_CHANGED", ""))

    if b_analysis.write_objects != a_analysis.write_objects:
        changes.append(Change(
            "WRITE_TARGET_CHANGED",
            f"{', '.join(b_analysis.write_objects) or '-'} -> {', '.join(a_analysis.write_objects) or '-'}",
        ))

    if not changes and before_clean.upper() != after_clean.upper():
        changes.append(Change("TEXTUAL_CHANGE_ONLY", "No supported structural difference detected."))

    return DiffResult(changes)
