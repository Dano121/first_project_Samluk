"""Extract: reading frozen order data from disk.

Lesson 8 had the same code as a function taking `raw_dir` and `pattern` on every call.
Here the directory is state of the object: it is passed once, to __init__, and every
method uses it. The glob pattern stays a constructor argument -- not a class attribute --
because the same class is instantiated twice: once for orders, once for order items.
"""

import csv
import logging
from pathlib import Path

from src.clients.base import OrdersSource
from src.errors import SourceError

logger = logging.getLogger(__name__)


class FilesOrdersSource(OrdersSource):
    """Reads every file matching a glob pattern from a directory and concatenates the rows."""

    def __init__(self, raw_dir: Path, pattern: str) -> None:
        self._raw_dir = Path(raw_dir)  # instance attribute: owned by this object
        self._pattern = pattern

    def read_file(self, path: Path) -> list[dict]:
        """Return the rows of one frozen CSV file."""
        try:
            with open(path, newline="", encoding="utf-8") as file:
                reader = csv.DictReader(file)
                return [row for row in reader]
        except (OSError, csv.Error) as error:
            # The csv/OS exception does not leave this layer: the caller gets pipeline
            # vocabulary and does not have to import csv to handle it.
            raise SourceError(f"{path.name} could not be read: {error}") from error

    def read_all(self) -> list[dict]:
        """Read every matching file, without hardcoding how many there are."""
        if not self._raw_dir.is_dir():
            raise SourceError(f"missing input data directory: {self._raw_dir}")

        rows: list[dict] = []
        for path in sorted(self._raw_dir.glob(self._pattern)):
            rows.extend(self.read_file(path))

        logger.info("read %d rows from %s (%s)", len(rows), self._raw_dir, self._pattern)
        return rows

    def __repr__(self) -> str:
        return f"FilesOrdersSource(raw_dir={str(self._raw_dir)!r}, pattern={self._pattern!r})"
