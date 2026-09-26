SELECT
    c.customer_id,
    o.order_id,
    o.amount
FROM customers c
LEFT JOIN orders o
    ON o.customer_id = c.customer_id
WHERE o.status IN ('OPEN', 'PENDING');
