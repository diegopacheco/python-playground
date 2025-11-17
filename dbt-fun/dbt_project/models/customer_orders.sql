SELECT
    c.customer_id,
    c.customer_name,
    c.country,
    o.order_id,
    o.product_name,
    o.quantity,
    o.price,
    o.order_date,
    (o.quantity * o.price) as total_amount
FROM {{ ref('customers') }} c
JOIN {{ ref('orders') }} o ON c.customer_id = o.customer_id
