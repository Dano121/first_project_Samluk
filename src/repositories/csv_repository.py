"""Load: writing rows into CSV files.

The same contract as the PostgreSQL repository, a completely different target. That is the
whole point of `OrdersRepository`: main.py swaps one line and neither the source nor the
transforms notice.

`write_rows()` is the function from Lesson 8, unchanged.
"""

import csv
import logging
from pathlib import Path

from src.decorators import log_step
from src.repositories.base import OrdersRepository

logger = logging.getLogger(__name__)

ORDERS_FILE = "orders.csv"
ITEMS_FILE = "order_items.csv"


class CsvOrdersRepository(OrdersRepository):
    """Writes both grains into two CSV files in one directory."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = Path(output_dir)

    @log_step
    def save(self, order_rows: list[dict], item_rows: list[dict]) -> dict:
        written = {
            "orders": self._write_rows(order_rows, self._output_dir / ORDERS_FILE),
            "items": self._write_rows(item_rows, self._output_dir / ITEMS_FILE),
        }
        logger.info("wrote %(orders)d orders and %(items)d items", written)
        return written

    def count_rows(self) -> dict:
        return {
            "orders": self._count_data_lines(self._output_dir / ORDERS_FILE),
            "items": self._count_data_lines(self._output_dir / ITEMS_FILE),
        }

    @staticmethod
    def _write_rows(rows: list[dict], path: Path) -> int:
        """Write rows to a CSV file and return how many were written."""
        if not rows:
            return 0

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        return len(rows)

    @staticmethod
    def _count_data_lines(path: Path) -> int:
        """Rows in the file, not counting the header."""
        if not path.exists():
            return 0
        with open(path, newline="", encoding="utf-8") as file:
            return sum(1 for _ in csv.DictReader(file))

    def __repr__(self) -> str:
        return f"CsvOrdersRepository(output_dir={str(self._output_dir)!r})"
