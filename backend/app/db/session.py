from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_schema() -> None:
    with engine.begin() as connection:
        existing = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(cases)")).fetchall()
        }
        additions = {
            "latest_recommendation_label": "ALTER TABLE cases ADD COLUMN latest_recommendation_label VARCHAR(128)",
            "latest_risk_level": "ALTER TABLE cases ADD COLUMN latest_risk_level VARCHAR(64)",
            "latest_recommendation_at": "ALTER TABLE cases ADD COLUMN latest_recommendation_at DATETIME",
            "latest_case_update_id": "ALTER TABLE cases ADD COLUMN latest_case_update_id INTEGER",
        }
        for column, ddl in additions.items():
            if column not in existing:
                connection.execute(text(ddl))
