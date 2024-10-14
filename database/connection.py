from airflow.hooks.base import BaseHook
from sqlalchemy import create_engine


def mariadb_connection(conn_id: str):
    conn = BaseHook.get_connection(conn_id)

    user = conn.login
    password = conn.password
    host = conn.host
    port = conn.port
    db = conn.schema

    engine_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db}"

    engine = create_engine(engine_string)

    return engine

