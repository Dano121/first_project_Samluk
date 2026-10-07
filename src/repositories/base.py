"""The contract every write target must fulfil.

The orchestrator calls `save()` and `count_rows()`. It does not know, and must not know,
whether the rows end up in PostgreSQL or in a CSV file.
"""

from abc import ABC, abstractmethod


class OrdersRepository(ABC):
    """Anything the pipeline can write its two grains of rows into."""

    @abstractmethod
    def save(self, order_rows: list[dict], item_rows: list[dict]) -> dict:
        """Persist both grains and return how many rows of each were written."""

    @abstractmethod
    def count_rows(self) -> dict:
        """Return how many rows each target currently holds."""

    def __enter__(self) -> "OrdersRepository":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        self.close()
        return False  # False -- do not swallow the exception, just release the resource

    def close(self) -> None:
        """Release whatever the repository holds. Nothing to do by default."""
