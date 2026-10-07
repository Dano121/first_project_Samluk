"""Load: writing rows into PostgreSQL.

The only module in the project that contains SQL. It knows table names, columns and
constraints -- and nothing about where the data came from or what shape it had on the way in.
"""

import logging

from psycopg2.extensions import connection as Connection
from psycopg2.extras import execute_values

from src.db.connection import describe_target
from src.decorators import log_step
from src.errors import DatabaseError
from src.repositories.base import OrdersRepository

logger = logging.getLogger(__name__)

# `%s` here is a PLACEHOLDER, not string formatting. The values travel to the database on
# a separate channel and never become part of the statement.
INSERT_ORDERS_SQL = """
    INSERT INTO ingest_orders
        (order_id, order_date, customer_id, amount, currency, status,
         customer_name, customer_city, customer_email, item_count, source)
    VALUES %s
    ON CONFLICT (order_id) DO UPDATE SET
        order_date     = EXCLUDED.order_date,
        customer_id    = EXCLUDED.customer_id,
        amount         = EXCLUDED.amount,
        currency       = EXCLUDED.currency,
        status         = EXCLUDED.status,
        customer_name  = EXCLUDED.customer_name,
        customer_city  = EXCLUDED.customer_city,
        customer_email = EXCLUDED.customer_email,
        item_count     = EXCLUDED.item_count,
        source         = EXCLUDED.source,
        ingested_at    = now()
"""

INSERT_ITEMS_SQL = """
    INSERT INTO ingest_order_items (order_id, position, sku, product_name, quantity, unit_price, line_total)
    VALUES %s
    ON CONFLICT (order_id, position) DO UPDATE SET
        sku          = EXCLUDED.sku,
        product_name = EXCLUDED.product_name,
        quantity     = EXCLUDED.quantity,
        unit_price   = EXCLUDED.unit_price,
        line_total   = EXCLUDED.line_total
"""

COUNT_ORDERS_SQL = "SELECT COUNT(*) FROM ingest_orders"
COUNT_ITEMS_SQL = "SELECT COUNT(*) FROM ingest_order_items"

ORDER_COLUMNS = (
    "order_id", "order_date", "customer_id", "amount", "currency", "status",
    "customer_name", "customer_city", "customer_email", "item_count", "source",
)
ITEM_COLUMNS = ("order_id", "position", "sku", "product_name", "quantity", "unit_price", "line_total")


class PostgresOrdersRepository(OrdersRepository):
    """Loads orders and their items into the target tables."""

    def __init__(self, connection: Connection) -> None:
        self._connection = connection

    @property
    def is_closed(self) -> bool:
        """Computed on access -- psycopg2 keeps the flag as 0/1, we hand out a bool."""
        return bool(self._connection.closed)

    @staticmethod
    def _as_tuples(rows: list[dict], columns: tuple[str, ...]) -> list[tuple]:
        """Dicts -> tuples in the column order the INSERT expects."""
        return [tuple(row[column] for column in columns) for row in rows]

    @log_step
    def save(self, order_rows: list[dict], item_rows: list[dict]) -> dict:
        """Write both grains in ONE transaction.

        Orders go in first: an item row points at an order through a foreign key, so
        the other order would fail on the very first insert.
        """
        try:
            # `with self._connection:` opens a TRANSACTION -- leaving it without an
            # exception commits, an exception rolls back. It does NOT close the connection.
            with self._connection, self._connection.cursor() as cursor:
                execute_values(
                    cursor, INSERT_ORDERS_SQL, self._as_tuples(order_rows, ORDER_COLUMNS)
                )
                execute_values(
                    cursor, INSERT_ITEMS_SQL, self._as_tuples(item_rows, ITEM_COLUMNS)
                )
        except Exception as error:
            raise DatabaseError(f"load into {describe_target()} failed: {error}") from error

        written = {"orders": len(order_rows), "items": len(item_rows)}
        logger.info("loaded %(orders)d orders and %(items)d items", written)
        return written

    def count_rows(self) -> dict:
        with self._connection.cursor() as cursor:
            cursor.execute(COUNT_ORDERS_SQL)
            orders = cursor.fetchone()[0]
            cursor.execute(COUNT_ITEMS_SQL)
            items = cursor.fetchone()[0]
        return {"orders": orders, "items": items}

    def close(self) -> None:
        if not self.is_closed:
            self._connection.close()
            logger.info("connection to %s closed", describe_target())

    def __repr__(self) -> str:
        return f"PostgresOrdersRepository(target={describe_target()!r}, closed={self.is_closed})"
