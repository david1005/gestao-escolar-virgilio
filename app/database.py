from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

def montar_database_url():
    database_url = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PRIVATE_URL")
    if database_url:
        return database_url.replace("postgres://", "postgresql://", 1)

    host = os.getenv("PGHOST")
    port = os.getenv("PGPORT", "5432")
    user = os.getenv("PGUSER")
    password = os.getenv("PGPASSWORD")
    database = os.getenv("PGDATABASE")
    if all([host, user, password, database]):
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    raise RuntimeError(
        "Banco de dados nao configurado. Defina DATABASE_URL no Railway ou vincule um servico PostgreSQL ao app."
    )

DATABASE_URL = montar_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
