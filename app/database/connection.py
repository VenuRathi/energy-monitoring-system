if __package__ is None or __package__ == "":
    from pathlib import Path
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import psycopg
from psycopg import Connection

from config.settings import Settings


def get_connection(settings: Settings) -> Connection:
    return psycopg.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )


"""
## FILE EXPLANATION
Purpose:
This file opens PostgreSQL connections.

Why this file exists:
Database connection logic should stay in one place so all database code uses
one standard setup.

What data enters the file:
Settings object with database host, port, name, user, and password.

What data leaves the file:
An open psycopg2 PostgreSQL connection object.

Which layer of the architecture it belongs to:
Database Layer.

How it interacts with other files:
Used by database/models.py and database/repositories.py through main.py setup.
"""
