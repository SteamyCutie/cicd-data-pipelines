WITH raw_totals AS (
    SELECT
        COUNT(*) AS orders_placed,
        SUM(CASE WHEN LOWER(TRIM(status)) = 'paid' THEN amount_cents ELSE 0 END) AS cents
    FROM {{ ref('orders') }}
),

mart_totals AS (
    SELECT
        SUM(orders_placed) AS orders_placed,
        SUM(revenue_cents) AS cents
    FROM {{ ref('fct_daily_revenue') }}
)

SELECT raw_totals.cents
FROM raw_totals
CROSS JOIN mart_totals
WHERE
    raw_totals.cents <> mart_totals.cents
    OR raw_totals.orders_placed <> mart_totals.orders_placed
