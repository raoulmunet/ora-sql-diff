# ora-sql-diff

[![tests](https://github.com/raoulmunet/ora-sql-diff/actions/workflows/tests.yml/badge.svg)](https://github.com/raoulmunet/ora-sql-diff/actions/workflows/tests.yml) ![Python](https://img.shields.io/badge/Python-3.10--3.13-blue) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Compare two Oracle SQL statements by **structure**, not only by text.

> **Oracle compatibility**
>
> | Oracle version | Support |
> |---|---|
> | Oracle Database 19c | ✅ Common SQL structures |
> | Oracle Database 23ai | ✅ Common SQL structures |
> | Oracle AI Database 26ai | ✅ Common SQL structures |
>
> The current release performs offline structural analysis using syntax common across these releases. Version-specific constructs that are not recognized are preserved in normalized text but may not receive a dedicated semantic change category.

## Why this tool exists

Traditional diffs are noisy for SQL because formatting changes can dominate the output.

These two statements are textually different:

```sql
SELECT a,b FROM t WHERE x=1;
```

```sql
SELECT
    a,
    b
FROM t
WHERE x = 1;
```

but structurally they are very similar.

`ora-sql-diff` instead focuses on changes such as:

- table added or removed;
- projected column added or removed;
- JOIN type changed;
- JOIN target changed;
- WHERE clause changed;
- GROUP BY / ORDER BY added, removed or changed;
- DML target changed.

## Installation

```bash
python -m pip install "git+https://github.com/raoulmunet/ora-sql-diff.git"
```

## Usage

```bash
ora-sql-diff before.sql after.sql
ora-sql-diff before.sql after.sql --format json
```

Example:

**before.sql**

```sql
SELECT c.customer_id, o.order_id
FROM customers c
JOIN orders o ON o.customer_id = c.customer_id
WHERE o.status = 'OPEN';
```

**after.sql**

```sql
SELECT c.customer_id, o.order_id, o.amount
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE o.status IN ('OPEN', 'PENDING');
```

Possible output:

```text
PROJECTION_ADDED: O.AMOUNT
JOIN_TYPE_CHANGED: ORDERS INNER -> LEFT
WHERE_CHANGED
```

## Important limitation

This is **not a theorem prover** and does not claim semantic equivalence.

For example, these can be semantically equivalent while looking structurally different:

- `EXISTS` vs `JOIN`;
- `IN` vs `EXISTS`;
- equivalent predicate rewrites;
- CTE vs inline view;
- logically equivalent boolean expressions.

The tool reports structural change categories that are useful during code review.

## Python API

```python
from ora_sql_diff import compare_sql

result = compare_sql(before_sql, after_sql)

for change in result.changes:
    print(change.kind, change.detail)
```

## Roadmap

- better CTE-aware comparison;
- predicate normalization;
- MERGE-aware change analysis;
- HTML report;
- GitHub pull-request integration.

## Oracle Dev Tools family

This repository is part of the **Oracle Dev Tools** suite: small, composable developer utilities designed around Oracle Database 19c, 23ai and 26ai.

| Area | Tools |
|---|---|
| Foundation | [ora-core](https://github.com/raoulmunet/ora-core) |
| SQL analysis | [ora-impact](https://github.com/raoulmunet/ora-impact) · [ora-plan](https://github.com/raoulmunet/ora-plan) · [ora-lineage](https://github.com/raoulmunet/ora-lineage) · [ora-lint](https://github.com/raoulmunet/ora-lint) · [ora-sql-diff](https://github.com/raoulmunet/ora-sql-diff) · [ora-sql-complexity](https://github.com/raoulmunet/ora-sql-complexity) · [ora-join-viz](https://github.com/raoulmunet/ora-join-viz) · [ora-bind](https://github.com/raoulmunet/ora-bind) |
| Data & operations | [ora-doc](https://github.com/raoulmunet/ora-doc) · [ora-data-quality](https://github.com/raoulmunet/ora-data-quality) · [ora-csv-loader](https://github.com/raoulmunet/ora-csv-loader) · [ora-etl-log](https://github.com/raoulmunet/ora-etl-log) · [ora-migration-check](https://github.com/raoulmunet/ora-migration-check) · [ora-errors](https://github.com/raoulmunet/ora-errors) · [ora-schema-explorer](https://github.com/raoulmunet/ora-schema-explorer) |
| PL/SQL analysis | [ora-exception-flow](https://github.com/raoulmunet/ora-exception-flow) · [ora-call-graph](https://github.com/raoulmunet/ora-call-graph) · [ora-dead-code](https://github.com/raoulmunet/ora-dead-code) |

## License

MIT.
