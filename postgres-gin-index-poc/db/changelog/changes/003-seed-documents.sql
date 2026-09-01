--liquibase formatted sql

--changeset diegopacheco:004-seed-known-documents
INSERT INTO documents (name, data) VALUES
('laptop-x1', '{"sku":"SKU-LAPTOP","category":"electronics","brand":"acme","price":1999.99,"tags":["portable","work"],"stock":{"warehouse":"wh-1","qty":7}}'),
('phone-p9',  '{"sku":"SKU-PHONE","category":"electronics","brand":"acme","price":899.50,"tags":["portable","mobile"],"stock":{"warehouse":"wh-2","qty":41}}'),
('desk-oak',  '{"sku":"SKU-DESK","category":"furniture","brand":"woodly","price":450.00,"tags":["office"],"stock":{"warehouse":"wh-1","qty":3},"discontinued":true}');
--rollback DELETE FROM documents WHERE name IN ('laptop-x1','phone-p9','desk-oak');

--changeset diegopacheco:005-seed-bulk-documents
INSERT INTO documents (name, data)
SELECT
    'product-' || i,
    jsonb_build_object(
        'sku', 'SKU-' || i,
        'category', (ARRAY['tools','books','games','food'])[1 + (i % 4)],
        'brand', 'brand-' || (i % 20),
        'price', ((i % 1000) + 0.99),
        'tags', to_jsonb(ARRAY['bulk', 'gen-' || (i % 10)]),
        'stock', jsonb_build_object('warehouse', 'wh-' || (i % 5), 'qty', i % 50)
    )
FROM generate_series(1, 50000) AS i;
--rollback DELETE FROM documents WHERE name LIKE 'product-%';
