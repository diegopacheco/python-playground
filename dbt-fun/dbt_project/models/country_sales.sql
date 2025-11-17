SELECT
    country,
    COUNT(DISTINCT customer_id) as customer_count,
    SUM(total_amount) as total_revenue,
    AVG(total_amount) as avg_order_value
FROM {{ ref('customer_orders') }}
GROUP BY country
ORDER BY total_revenue DESC
