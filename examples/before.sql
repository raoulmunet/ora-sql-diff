SELECT
    c.customer_id,
    o.order_id
FROM customers c
JOIN orders o
    ON o.customer_id = c.customer_id
WHERE o.status = 'OPEN';
