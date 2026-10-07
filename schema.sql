CREATE TABLE IF NOT EXISTS ingest_orders (
    order_id       TEXT           PRIMARY KEY,
    order_date     DATE           NOT NULL,
    customer_id    TEXT           NOT NULL,
    amount         NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
    currency       TEXT           NOT NULL,
    status         TEXT           NOT NULL CHECK (status IN ('paid', 'pending', 'shipped', 'cancelled')),
    customer_name  TEXT           NOT NULL,
    customer_city  TEXT           NOT NULL,
    customer_email TEXT           NOT NULL,
    item_count     INTEGER        NOT NULL CHECK (item_count >= 0),
    source         TEXT           NOT NULL,
    ingested_at    TIMESTAMPTZ    NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingest_order_items (
    order_id     TEXT           NOT NULL REFERENCES ingest_orders (order_id) ON DELETE CASCADE,
    position     INTEGER        NOT NULL CHECK (position > 0),
    sku          TEXT           NOT NULL,
    product_name TEXT           NOT NULL,
    quantity     INTEGER        NOT NULL,
    unit_price   NUMERIC(12, 2) NOT NULL,
    line_total   NUMERIC(12, 2) NOT NULL,
    PRIMARY KEY (order_id, position)
);
