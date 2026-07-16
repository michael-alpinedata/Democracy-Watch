from os import getenv
import psycopg

from sqlalchemy import URL, create_engine, pool

import src.models  # noqa: F401  # pyright: ignore[reportUnusedImport]
from src.models.base import Base


def _get_db_url(database=None):
    PG_USER = getenv("PG_USER")
    PG_PWD = getenv("PG_PWD")
    # Si aucun nom de db n'est fourni, on prend celle du .env
    PG_DB = database or getenv("PG_DB")
    PG_HOST = getenv("PG_HOST", "localhost")
    PG_PORT = getenv("PG_PORT", "5432")
    return URL.create(
        drivername="postgresql+psycopg",
        username=PG_USER,
        password=PG_PWD,
        host=PG_HOST,
        port=int(PG_PORT),
        database=PG_DB,
    )


def get_engine():
    """Return a configured SQLAlchemy engine"""
    PG_ECHO = getenv("PG_ECHO", False)
    pg_url = _get_db_url()
    return create_engine(pg_url, poolclass=pool.NullPool, echo=bool(PG_ECHO))


def create_db():
    """Drop the current DB and recreate from the schema."""
    print("Creating DB")
    
    target_db = getenv("PG_DB")
    
    # 1. Connexion à la base "postgres" par défaut pour créer/recréer la db cible
    # On passe autocommit=True car PostgreSQL interdit le 'CREATE/DROP DATABASE' dans une transaction
    url_postgres = _get_db_url(database="postgres")
    
    print(f"Checking/Creating database '{target_db}'...")
    with psycopg.connect(
        host=url_postgres.host,
        port=url_postgres.port,
        user=url_postgres.username,
        password=url_postgres.password,
        dbname="postgres",
        autocommit=True
    ) as conn:
        with conn.cursor() as cur:
            # On supprime la db si elle existe (simule le drop_all global)
            cur.execute(f'DROP DATABASE IF EXISTS "{target_db}" WITH (FORCE);')
            # On la recrée à neuf
            cur.execute(f'CREATE DATABASE "{target_db}";')

    # 2. Maintenant qu'elle existe, SQLAlchemy peut s'y connecter normalement
    engine = get_engine()
    print(Base.metadata.tables)
    
    # Plus besoin de drop_all vu qu'on vient de drop la DB entière
    Base.metadata.create_all(engine)
    
    print("Db was created")
    return Base.metadata.tables


def get_tables_definition():
    return Base.metadata.sorted_tables