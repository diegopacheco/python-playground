SELECT
    customer_id,
    customer_name,
    country,
    COUNT(order_id) as total_orders,
    SUM(total_amount) as total_spent,
    AVG(total_amount) as avg_order_value
FROM {{ ref('customer_orders') }}
GROUP BY customer_id, customer_name, country
ORDER BY total_spent DESC
