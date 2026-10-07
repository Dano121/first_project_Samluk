"""Project paths, database settings and constants -- one place instead of literals
scattered across modules."""

import os
from pathlib import Path

# The project directory is derived from the location of THIS file, not from the working
# directory -- so the pipeline behaves the same from a terminal and from a scheduler.
PROJECT_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_DIR / "data" / "raw"
CURATED_DIR = PROJECT_DIR / "data" / "curated"
REJECTED_DIR = PROJECT_DIR / "data" / "rejected"
FIXTURES_DIR = PROJECT_DIR.parent / "fixtures"

ORDERS_PATTERN = "orders_*.csv"
ORDER_ITEMS_PATTERN = "order_items_*.csv"
CUSTOMERS_FILENAME = "customers.json"

ALLOWED_STATUSES = {"paid", "pending", "shipped", "cancelled"}
REQUIRED_ORDER_FIELDS = ["order_id", "customer_id", "amount", "status"]

DEFAULT_CURRENCY = "PLN"
DEFAULT_ADDRESS = "Brak adresu"
DEFAULT_CONTACTS = "Brak email lub nr telefonu"

SOURCE_NAME = "homework-store"
UNKNOWN_CATEGORY = "UNKNOWN"

# Connection settings come from the environment, with defaults that match the course
# container. The password is read, never written down here.
DB_CONFIG = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", "5432")),
    "dbname": os.environ.get("PGDATABASE", "de_fundamentals"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD", "password"),
}
