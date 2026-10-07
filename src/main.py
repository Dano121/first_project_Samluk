"""Entry point of the pipeline: wires the layers together, holds no business logic.

Run it from the project directory:

    uv run python -m src.main
"""

import logging

from src.clients.base import OrdersSource
from src.clients.customers_file_source import read_customers
from src.clients.files_source import FilesOrdersSource
from src.config import CURATED_DIR, CUSTOMERS_FILENAME, ORDERS_PATTERN, ORDER_ITEMS_PATTERN, RAW_DIR
from src.db.connection import get_connection
from src.errors import PipelineError, ValidationError
from src.repositories.base import OrdersRepository
from src.repositories.csv_repository import CsvOrdersRepository  # noqa: F401  -- swap-in
from src.repositories.postgres_repository import PostgresOrdersRepository
from src.transforms.cleaning import clean_order, clean_order_item
from src.transforms.orders import normalize_all
from src.transforms.validation import validate_order

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def build_orders_source() -> OrdersSource:
    """The one place that decides WHERE the orders come from."""
    return FilesOrdersSource(RAW_DIR, ORDERS_PATTERN)


def build_order_items_source() -> OrdersSource:
    """The one place that decides WHERE the order items come from.

    Same class as build_orders_source() -- only the glob pattern differs -- because
    reading "many frozen files, one flat list" is one shape used for two grains.
    """
    return FilesOrdersSource(RAW_DIR, ORDER_ITEMS_PATTERN)


def build_repository() -> OrdersRepository:
    """The one place that decides WHERE the result goes.

    Swap this single line for `CsvOrdersRepository(CURATED_DIR)` and the whole pipeline
    writes files instead of rows -- without touching the source or the transforms.
    """
    return PostgresOrdersRepository(get_connection())


def clean_and_validate_orders(raw_orders: list[dict]) -> tuple[list[dict], list[dict]]:
    """Clean and validate orders one by one; a bad order is rejected, not fatal."""
    seen_ids: set[str] = set()
    cleaned_orders = []
    rejected_orders = []
    for raw_order in raw_orders:
        try:
            cleaned = clean_order(raw_order)
            validate_order(cleaned, seen_ids)
            cleaned_orders.append(cleaned)
        except ValidationError as error:
            rejected_orders.append({"order_id": raw_order["order_id"], "reason": str(error)})
    return cleaned_orders, rejected_orders


def clean_order_items(raw_items: list[dict]) -> list[dict]:
    """Clean order items one by one; a bad item is silently dropped."""
    cleaned_items = []
    for raw_item in raw_items:
        try:
            cleaned_items.append(clean_order_item(raw_item))
        except ValidationError:
            pass
    return cleaned_items


def run(
    orders_source: OrdersSource,
    order_items_source: OrdersSource,
    repository: OrdersRepository,
) -> dict:
    """Run the whole ingestion and return a summary of the run."""
    raw_orders = orders_source.read_all()                       # extract
    raw_items = order_items_source.read_all()                   # extract
    customers = read_customers(RAW_DIR / CUSTOMERS_FILENAME)    # extract

    cleaned_orders, rejected_orders = clean_and_validate_orders(raw_orders)  # clean + validate
    cleaned_items = clean_order_items(raw_items)                             # clean

    order_rows, item_rows = normalize_all(cleaned_orders, cleaned_items, customers)  # transform

    with repository:                                             # load
        written = repository.save(order_rows, item_rows)
        in_target = repository.count_rows()

    return {
        "read": len(raw_orders),
        "rejected": len(rejected_orders),
        "written": written,
        "in_target": in_target,
    }


def main() -> None:
    """Run the pipeline and report the result; a pipeline error ends with exit code 1."""
    configure_logging()

    try:
        summary = run(build_orders_source(), build_order_items_source(), build_repository())
    except PipelineError as error:
        logger.error("run aborted -- %s: %s", type(error).__name__, error)
        raise SystemExit(1) from error

    logger.info(
        "summary: read=%d, rejected=%d, written=%s, in target=%s",
        summary["read"],
        summary["rejected"],
        summary["written"],
        summary["in_target"],
    )


if __name__ == "__main__":
    main()
