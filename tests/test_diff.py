from ora_sql_diff import compare_sql


def test_formatting_only_change_is_ignored():
    before = "SELECT a,b FROM t WHERE x=1;"
    after = """
    SELECT
      a,
      b
    FROM t
    WHERE x = 1;
    """
    r = compare_sql(before, after)
    assert not any(c.kind.startswith("PROJECTION_") for c in r.changes)
    assert not any(c.kind.startswith("OBJECT_") for c in r.changes)


def test_projection_and_join_type_change():
    before = """
    SELECT c.customer_id, o.order_id
    FROM customers c
    JOIN orders o ON o.customer_id = c.customer_id
    WHERE o.status = 'OPEN'
    """
    after = """
    SELECT c.customer_id, o.order_id, o.amount
    FROM customers c
    LEFT JOIN orders o ON o.customer_id = c.customer_id
    WHERE o.status IN ('OPEN', 'PENDING')
    """
    r = compare_sql(before, after)
    kinds = {c.kind for c in r.changes}
    assert "PROJECTION_ADDED" in kinds
    assert "JOIN_TYPE_CHANGED" in kinds
    assert "WHERE_CHANGED" in kinds
