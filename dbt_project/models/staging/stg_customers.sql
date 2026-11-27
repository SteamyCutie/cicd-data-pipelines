SELECT
    customer_id,
    LOWER(TRIM(segment)) AS segment
FROM {{ ref('customers') }}
