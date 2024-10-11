import numpy as np
from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker

from database.connection import mariadb_connection
from database.schema import AwsStnInfo, AwsData, CloudData, TemperatureData, VisibleData
from airflow.models.param import ParamsDict


def insert_data(group_id, task_id, stn, **kwargs):
    schemas = {
        'aws': AwsData,
        'cloud': CloudData,
        'visible': VisibleData,
        'temperature': TemperatureData
    }

    try:
        p: ParamsDict = kwargs["params"]
        conn_id = p["conn_id"]

        engine = mariadb_connection(conn_id)
        session_ = sessionmaker(bind=engine)
        session = session_()

        if group_id == 'Preprocessing_group':
            task_id_temp = task_id.split('_')[0]
            schema = schemas.get(task_id_temp, None)
        elif group_id == 'cloud_group':
            schema = CloudData

        if schema is None:
            raise ValueError('group_id is not correct')

        data = kwargs['ti'].xcom_pull(task_ids=f'{group_id}.{task_id}', key=f'{stn}_data')
        print(f"Pulled data: {data}")  # Debugging line to check pulled data

        if data is None:
            raise ValueError('Data is not exists')
        data = data.to_dict("records")

        for n, r in enumerate(data):
            for key, value in data[n].items():
                if isinstance(value, float) and np.isnan(value):
                    data[n][key] = None

        for d in data:
            duplicated_data = session.query(schema).filter(and_(schema.STN_ID == d['STN_ID'],
                                                                schema.CR_YMD == d['CR_YMD'])).first()
            if duplicated_data:
                print(f'중복 데이터:{d["CR_YMD"]}')
                continue

            session.add(schema(**d))

        session.commit()
        session.close()

    except Exception as e:
        session.rollback()
        raise IOError(f'삽입 실패! : {e}')


def checking_stn_id(stn, **kwargs):
    p: ParamsDict = kwargs["params"]
    conn_id = p["conn_id"]
    try:
        engine = mariadb_connection(conn_id)
        session_ = sessionmaker(bind=engine)
        session = session_()

        result = session.query(AwsStnInfo).filter(AwsStnInfo.STN_ID == stn).all()
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
