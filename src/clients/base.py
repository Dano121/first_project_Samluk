"""The contract every orders source must fulfil.

An ABC is a class that cannot be instantiated on its own. `@abstractmethod` marks a method
that every subclass has to implement -- and Python refuses to build an object of a class
that skipped one.
"""

from abc import ABC, abstractmethod


class OrdersSource(ABC):
    """Anything that can hand the pipeline a list of raw order records."""

    @abstractmethod
    def read_all(self) -> list[dict]:
        """Return every raw order record this source has."""
