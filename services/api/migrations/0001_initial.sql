-- Street CEO API persistence starting point.
-- Apply with a migration runner in deployment; this file is intentionally
-- additive and contains no destructive operations.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS shops (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name varchar(120) NOT NULL,
    currency char(3) NOT NULL,
    timezone varchar(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id uuid NOT NULL REFERENCES shops(id),
    sku varchar(64) NOT NULL,
    name varchar(120) NOT NULL,
    unit_price_cents bigint NOT NULL CHECK (unit_price_cents >= 0),
    stock_qty bigint NOT NULL CHECK (stock_qty >= 0),
    UNIQUE (shop_id, sku)
);

CREATE TABLE IF NOT EXISTS sales (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id uuid NOT NULL REFERENCES shops(id),
    tender varchar(32) NOT NULL,
    total_cents bigint NOT NULL CHECK (total_cents >= 0),
    created_at timestamptz NOT NULL,
    idempotency_key varchar(255) NOT NULL,
    request_fingerprint char(64) NOT NULL,
    UNIQUE (shop_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS sale_lines (
    sale_id uuid NOT NULL REFERENCES sales(id),
    product_id uuid NOT NULL REFERENCES products(id),
    quantity bigint NOT NULL CHECK (quantity > 0),
    unit_price_cents bigint NOT NULL CHECK (unit_price_cents >= 0),
    PRIMARY KEY (sale_id, product_id)
);
