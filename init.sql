CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_name TEXT NOT NULL,
    product TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    address TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO orders (customer_name, product, status, address, created_at)
SELECT
    'Customer ' || i,
    'Product ' || (floor(random() * 100) + 1),
    CASE WHEN random() < 0.7 THEN 'recieved'
         WHEN random() < 0.9 THEN 'pending'
         ELSE 'processed' END,
    'Address ' || (floor(random() * 1000) + 1),
    CURRENT_TIMESTAMP - (floor(random() * 30) || ' days')::interval
FROM generate_series(1, 10000) AS s(i);
