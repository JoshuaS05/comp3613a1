import logging
import threading
import time
from contextlib import contextmanager

from sqlalchemy import Date, DateTime, Integer, String, Time, inspect, text
from sqlalchemy.exc import DBAPIError, OperationalError, ProgrammingError
from sqlmodel import SQLModel, Session, create_engine

from app.config import get_settings

logger = logging.getLogger(__name__)

_schema_lock = threading.Lock()


def sqlalchemy_uri(uri: str) -> str:
    """Accept Render's postgres:// URLs in the sync SQLAlchemy engine."""
    if uri.startswith("postgres://"):
        return "postgresql+psycopg2://" + uri[len("postgres://") :]
    if uri.startswith("postgresql://"):
        return "postgresql+psycopg2://" + uri[len("postgresql://") :]
    return uri


engine = create_engine(
    sqlalchemy_uri(get_settings().database_uri),
    echo=get_settings().env.lower()
    in ["dev", "development", "test", "testing", "staging"],
    pool_size=get_settings().db_pool_size,
    max_overflow=get_settings().db_additional_overflow,
    pool_timeout=get_settings().db_pool_timeout,
    pool_recycle=get_settings().db_pool_recycle,
)


def create_db_and_tables() -> None:
    # Ensure model modules are imported so tables are registered on metadata.
    import app.models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _upgrade_review_table()
    _upgrade_presentation_table()


def _upgrade_review_table() -> None:
    inspector = inspect(engine)
    if "review" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("review")
    }
    column_types = {
        "feedback": String(),
        "decision": String(),
        "reviewed_at": DateTime(),
        "submission_id": Integer(),
        "reviewer_id": Integer(),
    }
    references = {
        "submission_id": ' REFERENCES "submission" (id)',
        "reviewer_id": ' REFERENCES "user" (id)',
    }

    with engine.begin() as connection:
        for column_name, column_type in column_types.items():
            if column_name in existing_columns:
                continue
            sql_type = column_type.compile(dialect=engine.dialect)
            reference = references.get(column_name, "")
            connection.execute(
                text(
                    f'ALTER TABLE "review" ADD COLUMN "{column_name}" '
                    f"{sql_type}{reference}"
                )
            )

        current_inspector = inspect(connection)
        unique_constraints = current_inspector.get_unique_constraints("review")
        indexes = current_inspector.get_indexes("review")
        has_submission_unique = any(
            constraint.get("column_names") == ["submission_id"]
            for constraint in unique_constraints
        ) or any(
            index.get("column_names") == ["submission_id"] and index.get("unique")
            for index in indexes
        )
        if not has_submission_unique:
            connection.execute(
                text(
                    'CREATE UNIQUE INDEX IF NOT EXISTS '
                    '"uq_review_submission_id" ON "review" ("submission_id")'
                )
            )


def _upgrade_presentation_table() -> None:
    inspector = inspect(engine)
    if "presentation" not in inspector.get_table_names():
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("presentation")
    }
    column_types = {
        "date": Date(),
        "time": Time(),
        "location": String(),
        "submission_id": Integer(),
    }

    with engine.begin() as connection:
        for column_name, column_type in column_types.items():
            if column_name in existing_columns:
                continue
            sql_type = column_type.compile(dialect=engine.dialect)
            reference = (
                ' REFERENCES "submission" (id)'
                if column_name == "submission_id"
                else ""
            )
            connection.execute(
                text(
                    f'ALTER TABLE "presentation" ADD COLUMN "{column_name}" '
                    f"{sql_type}{reference}"
                )
            )

        current_inspector = inspect(connection)
        unique_constraints = current_inspector.get_unique_constraints("presentation")
        indexes = current_inspector.get_indexes("presentation")
        has_submission_unique = any(
            constraint.get("column_names") == ["submission_id"]
            for constraint in unique_constraints
        ) or any(
            index.get("column_names") == ["submission_id"] and index.get("unique")
            for index in indexes
        )
        if not has_submission_unique:
            connection.execute(
                text(
                    'CREATE UNIQUE INDEX IF NOT EXISTS '
                    '"uq_presentation_submission_id" '
                    'ON "presentation" ("submission_id")'
                )
            )


def drop_all() -> None:
    SQLModel.metadata.drop_all(bind=engine)


def is_db_not_ready_error(exc: BaseException) -> bool:
    """True when Postgres is unreachable or the schema/tables are missing."""
    if isinstance(exc, OperationalError):
        return True
    if isinstance(exc, ProgrammingError):
        return True
    if isinstance(exc, DBAPIError) and getattr(exc, "connection_invalidated", False):
        return True

    text = str(exc).lower()
    markers = (
        "does not exist",
        "undefinedtable",
        "undefined table",
        "no such table",
        "relation ",
        "could not connect",
        "connection refused",
        "connection timed out",
        "server closed the connection",
        "the database system is starting up",
        "remaining connection slots",
        "too many connections",
        "ssl connection has been closed",
    )
    return any(m in text for m in markers)


def ensure_db_and_tables(
    *,
    retries: int = 8,
    delay_seconds: float = 2.0,
) -> None:
    """Create tables, retrying while the prod DB is still coming up."""
    last: BaseException | None = None
    for attempt in range(1, retries + 1):
        try:
            with _schema_lock:
                create_db_and_tables()
            if attempt > 1:
                logger.info("Database schema ready after %s attempt(s)", attempt)
            return
        except Exception as exc:  # noqa: BLE001 — first-boot resilience
            last = exc
            if not is_db_not_ready_error(exc) or attempt >= retries:
                raise
            logger.warning(
                "Database not ready (attempt %s/%s): %s",
                attempt,
                retries,
                exc,
            )
            time.sleep(delay_seconds * attempt)
    if last is not None:
        raise last


def recover_if_uninitialized(exc: BaseException) -> bool:
    """If *exc* looks like a missing schema, create tables and return True."""
    if not is_db_not_ready_error(exc):
        return False
    logger.warning("Uninitialized database detected; creating tables: %s", exc)
    ensure_db_and_tables()
    return True


def _session_generator():
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()


def get_session():
    yield from _session_generator()


@contextmanager
def get_cli_session():
    yield from _session_generator()
