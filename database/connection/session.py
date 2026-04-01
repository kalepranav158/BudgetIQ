from __future__ import annotations

from django.db import connection


def init_db() -> None:
    """Initialize Django database connection."""
    # Django initializes database automatically via DATABASES config
    pass


def get_db():
    """Get Django database connection object."""
    return connection


def get_db_session():
    """Get a database cursor for raw SQL operations."""
    return connection.cursor()
