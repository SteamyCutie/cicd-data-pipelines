SELECT order_id
FROM {{ ref('stg_orders') }}
WHERE amount_cents < 0
