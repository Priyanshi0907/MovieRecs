import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "movies.db"))

# Deployment-ready: honor DATABASE_URL if set (e.g. a managed Postgres URL in
# production), otherwise fall back to the local SQLite file for development.
# SQLite is fine for local dev/demo use but doesn't handle concurrent writes
# well under real production load - set DATABASE_URL to a Postgres connection
# string when deploying for real traffic.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_lightweight_migrations():
    """
    Base.metadata.create_all() only creates missing TABLES, not missing
    COLUMNS on tables that already exist. Since this project doesn't use a
    full migration framework (Alembic), this adds any new columns introduced
    after a database already exists - so upgrading the app doesn't require
    wiping production data. Safe to call every startup; it's a no-op once
    columns already exist.
    """
    inspector = inspect(engine)
    if "movies" not in inspector.get_table_names():
        return  # table doesn't exist yet - create_all() will handle it fresh

    existing_columns = {col["name"] for col in inspector.get_columns("movies")}
    migrations = {
        "embedding": "ALTER TABLE movies ADD COLUMN embedding JSON",
    }
    with engine.connect() as conn:
        for column_name, ddl in migrations.items():
            if column_name not in existing_columns:
                try:
                    conn.execute(text(ddl))
                    conn.commit()
                    print(f"Migration: added missing column '{column_name}' to movies table.")
                except Exception as e:
                    print(f"Migration warning: could not add column '{column_name}': {e}")