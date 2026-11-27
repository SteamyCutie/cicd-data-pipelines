SELECT
    o.order_date,
    c.segment,
    COUNT(*) AS orders_placed,
    SUM(CASE WHEN o.status = 'paid' THEN o.amount_cents ELSE 0 END) AS revenue_cents
FROM {{ ref('stg_orders') }} AS o
INNER JOIN {{ ref('stg_customers') }} AS c ON o.customer_id = c.customer_id
GROUP BY o.order_date, c.segment
