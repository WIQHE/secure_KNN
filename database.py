import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from sqlalchemy.exc import OperationalError

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:password@localhost:5432/secure_knn")

try:
    engine = create_engine(DATABASE_URL)
    # Perform a quick test connection
    conn = engine.connect()
    conn.close()
except OperationalError as e:
    if "postgresql" in DATABASE_URL:
        print("⚠️ PostgreSQL is not reachable. Falling back to local SQLite database: sqlite:///./secure_knn_dev.db")
        DATABASE_URL = "sqlite:///./secure_knn_dev.db"
        engine = create_engine(DATABASE_URL)
    else:
        raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
