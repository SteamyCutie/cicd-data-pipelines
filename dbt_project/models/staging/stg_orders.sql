SELECT
    order_id,
    customer_id,
    amount_cents,
    CAST(order_date AS DATE) AS order_date,
    LOWER(TRIM(status)) AS status
FROM {{ ref('orders') }}
