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

CREATE TABLE IF NOT EXISTS invoices (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id uuid NOT NULL REFERENCES shops(id),
    filename varchar(240) NOT NULL,
    content_type varchar(80) NOT NULL,
    size_bytes bigint NOT NULL CHECK (size_bytes > 0 AND size_bytes <= 10485760),
    sha256 char(64) NOT NULL,
    storage_backend varchar(20) NOT NULL,
    storage_ref varchar(255) NOT NULL,
    extraction_status varchar(32) NOT NULL,
    extraction_source varchar(32) NOT NULL,
    uploaded_at timestamptz NOT NULL,
    confirmed_at timestamptz
);

CREATE TABLE IF NOT EXISTS invoice_lines (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id uuid NOT NULL REFERENCES invoices(id),
    shop_id uuid NOT NULL REFERENCES shops(id),
    description varchar(240) NOT NULL,
    sku varchar(64),
    quantity bigint NOT NULL CHECK (quantity > 0),
    line_total_cents bigint NOT NULL CHECK (line_total_cents >= 0),
    calculated_unit_cost_micros bigint CHECK (calculated_unit_cost_micros >= 0),
    suggested_product_id uuid REFERENCES products(id),
    matched_product_id uuid REFERENCES products(id),
    match_status varchar(20) NOT NULL,
    source varchar(32) NOT NULL,
    evidence_ref varchar(240)
);

ALTER TABLE products ADD COLUMN IF NOT EXISTS unit_cost_micros bigint CHECK (unit_cost_micros >= 0);
ALTER TABLE products ADD COLUMN IF NOT EXISTS cost_source_invoice_id uuid;

CREATE TABLE IF NOT EXISTS product_cost_audits (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id uuid NOT NULL REFERENCES shops(id),
    product_id uuid NOT NULL REFERENCES products(id),
    invoice_id uuid NOT NULL REFERENCES invoices(id),
    quantity_received bigint NOT NULL CHECK (quantity_received > 0),
    unit_cost_micros bigint NOT NULL CHECK (unit_cost_micros >= 0),
    previous_unit_cost_micros bigint CHECK (previous_unit_cost_micros >= 0),
    new_unit_cost_micros bigint NOT NULL CHECK (new_unit_cost_micros >= 0),
    stock_before bigint NOT NULL CHECK (stock_before >= 0),
    stock_after bigint NOT NULL CHECK (stock_after >= 0),
    recorded_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS product_cost_corrections (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id uuid NOT NULL REFERENCES shops(id),
    product_id uuid NOT NULL REFERENCES products(id),
    unit_cost_micros bigint NOT NULL CHECK (unit_cost_micros >= 0),
    effective_date date NOT NULL,
    reason varchar(500) NOT NULL,
    source_ref varchar(240) NOT NULL,
    actor varchar(80) NOT NULL,
    status varchar(20) NOT NULL,
    created_at timestamptz NOT NULL,
    confirmed_at timestamptz
);

CREATE TABLE IF NOT EXISTS sales (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id uuid NOT NULL REFERENCES shops(id),
    tender varchar(32) NOT NULL,
    total_cents bigint NOT NULL CHECK (total_cents >= 0),
    cogs_micros bigint CHECK (cogs_micros >= 0),
    created_at timestamptz NOT NULL,
    idempotency_key varchar(255) NOT NULL,
    request_fingerprint char(64) NOT NULL,
    UNIQUE (shop_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS operating_expenses (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_id uuid NOT NULL REFERENCES shops(id),
    category varchar(32) NOT NULL,
    frequency varchar(20) NOT NULL,
    occurred_on date NOT NULL,
    period_start date,
    period_end date,
    amount_cents bigint NOT NULL CHECK (amount_cents > 0),
    notes varchar(500) NOT NULL DEFAULT '',
    tender varchar(20) NOT NULL,
    status varchar(20) NOT NULL,
    created_at timestamptz NOT NULL,
    confirmed_at timestamptz,
    CHECK (period_end IS NULL OR period_start IS NOT NULL AND period_end >= period_start)
);

CREATE TABLE IF NOT EXISTS sale_lines (
    sale_id uuid NOT NULL REFERENCES sales(id),
    product_id uuid NOT NULL REFERENCES products(id),
    quantity bigint NOT NULL CHECK (quantity > 0),
    unit_price_cents bigint NOT NULL CHECK (unit_price_cents >= 0),
    PRIMARY KEY (sale_id, product_id)
);
