from itertools import islice
from typing import List, Any, Dict

import numpy as np
from sqlalchemy import and_, inspect, select, or_, text, insert
from sqlalchemy.orm import sessionmaker, scoped_session

from database.connection import mariadb_connection

from database.schema import AwsStnInfo, AwsData, CloudData, TemperatureData, VisibleData, WwData, AsosStnInfo, AsosData
from airflow.models.param import ParamsDict
from sqlalchemy.exc import SQLAlchemyError

schemas = {
    'aws_info': AwsStnInfo,
    'aws': AwsData,
    'cloud': CloudData,
    'visible': VisibleData,
    'temperature': TemperatureData,
    'ww': WwData,
    'asos_info': AsosStnInfo,
    'asos': AsosData
}


def clean_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    insert ignore를 사용하기 위한 Dict to List
    :param data:
    :return:
    """
    cleaned_data = []
    for item in data:
        cleaned_item = {}
        for key, value in item.items():
            if isinstance(value, float) and np.isnan(value):
                cleaned_item[key] = None
            else:
                cleaned_item[key] = value
            cleaned_data.append(cleaned_item)
    return cleaned_data


def check_and_create_table(kind='aws', **kwargs):
    """
    아직 작동 됨
    :param kind:
    :param conn_id:
    :return:
    """
    assert kind in ['aws', 'asos', 'cloud', 'visible', 'ww', 'temperature', 'aws_info', 'asos_info']

    p: ParamsDict = kwargs["params"]
    conn_id = p["conn_id"]
    schema = schemas.get(kind, None)
    if schema is None:
        raise ValueError('kind is not correct')

    try:
        engine = mariadb_connection(conn_id)
        inspector = inspect(engine)
        check_table = inspector.has_table(schema.__tablename__)
        if check_table:
            kwargs['ti'].xcom_push(key=f"check_table", value=True)
            print('Table is exists')
        else:
            kwargs['ti'].xcom_push(key=f"check_table", value=False)
            try:
                schema.__table__.create(bind=engine, checkfirst=True)
                print(f"Table {schema.__tablename__} created successfully")
            finally:
                engine.dispose()
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
    except KeyError as e:
        print(f"Missing parameter: {e}")
    except ImportError as e:
        print(f"Error importing models: {e}")


def insert_data(kind, group_id, task_id, stn, **kwargs):
    assert kind in ['aws', 'asos', 'cloud', 'visible', 'ww', 'temperature']
    schema = schemas.get(kind, None)
    if schema is None:
        raise ValueError('kind is not correct')

    try:
        p: ParamsDict = kwargs["params"]
        conn_id = p["conn_id"]

        engine = mariadb_connection(conn_id)
        session_ = sessionmaker(bind=engine,
                                expire_on_commit=False)

        # data = kwargs['ti'].xcom_pull(task_ids=f'{task_id}', key=f'{stn}_data')
        data = kwargs['ti'].xcom_pull(task_ids=f'{group_id}.{task_id}', key=f'{stn}_data')

        print(f"Pulled data: {data}")  # Debugging line to check pulled data

        if data is None:
            raise ValueError('Data is not exists')

        data = data.to_dict("records")
        data = clean_data(data)

        with session_() as session:
            total_inserted = 0
            try:
                stmt = insert(schema).prefix_with('IGNORE')
                result = session.execute(stmt, data)
                session.commit()

                total_inserted += result.rowcount

            except Exception as e:
                session.rollback()
                print(
                    f"Chunk 삽입 실패 - {conn_id} - {str(e)}"
                )

        print(f"Successfully inserted {total_inserted} records to {conn_id}")


    except Exception as e:
        session.rollback()
        raise IOError(f'삽입 실패! : {e}')


def checking_stn_id(kind, stn, **kwargs):
    assert kind in ['aws_info', 'asos_info']
    p: ParamsDict = kwargs["params"]
    conn_id = p["conn_id"]
    schema = schemas.get(kind, None)
    if schema is None:
        raise ValueError(f'kind is only aws_info, asos_info')
    try:
        engine = mariadb_connection(conn_id)
        session_ = sessionmaker(bind=engine)
        session = session_()

        result = session.query(schema).filter(schema.STN_ID == stn).all()
        if result:
            for row in result:
                print(f'STN_ID: {row.STN_ID}, STN_KO: {row.STN_KO}')
        else:
            raise ValueError('지점 번호가 존재하지 않습니다.')
        session.commit()
        session.close()
    except Exception as e:
        print(e)
        raise ValueError('지점 번호가 존재하지 않습니다.')
