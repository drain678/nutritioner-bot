"""File to run the database."""
import os

import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


def get_db_url() -> str:
    """Get database URL.

    Returns:
        str: URL fir database.
    """
    dotenv.load_dotenv()
    pg_vars = 'PG_HOST', 'PG_PORT', 'PG_USER', 'PG_PASSWORD', 'PG_DBNAME'
    credentials = {pg_var: os.environ.get(pg_var) for pg_var in pg_vars}
    return 'postgresql+psycopg://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DBNAME}'.format(**credentials)


def init_db():
    engine = create_engine(get_db_url())
    """Create tables in database."""
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal