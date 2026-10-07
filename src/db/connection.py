"""The only module that opens a connection to PostgreSQL.

Everything psycopg2-specific stops here. The rest of the project sees a connection object
and pipeline exceptions -- never `psycopg2.OperationalError`.
"""

import logging

import psycopg2
from psycopg2.extensions import connection as Connection

from src.config import DB_CONFIG
from src.decorators import retry
from src.errors import DatabaseError

logger = logging.getLogger(__name__)


def describe_target() -> str:
    """Human-readable connection target -- safe to log, contains no password."""
    return (
        f"{DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
        f"/{DB_CONFIG['dbname']}"
    )


# Retry only OperationalError -- a database that is still starting up is worth a second
# attempt. A syntax error or a wrong password is not, and is not retried.
@retry(max_attempts=3, delay=1.0, exceptions=(psycopg2.OperationalError,))
def _connect() -> Connection:
    return psycopg2.connect(**DB_CONFIG)


def get_connection() -> Connection:
    """Open a connection, or fail with a message that says what to check."""
    try:
        connection = _connect()
    except psycopg2.OperationalError as error:
        raise DatabaseError(
            f"cannot connect to {describe_target()} -- "
            "check whether the 'postgres-de' container is running: docker ps"
        ) from error

    logger.info("connected to %s", describe_target())
    return connection
