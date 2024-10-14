import requests
import pandas as pd
from airflow.models.param import ParamsDict
from database.connection import mariadb_connection
from sqlalchemy.orm import sessionmaker
from database.schema import AwsStnInfo
import numpy as np
import time
from requests.exceptions import RequestException
from aws_bins.collector import response_data


def stn_info_data(task_id, **kwargs):
    def process_case(case):
        # 공백을 기준으로 문자열을 분리하고, 빈 문자열을 제거
        split_case = list(filter(None, case.split(' ')))

        # 한국어명 이후에 영어명이 두 단어인 특이 케이스 처리
        if len(split_case) == 14:  # 특이 케이스는 총 15개의 항목이 됨
            split_case[9] = ' '.join(split_case[9:11])  # 'Gangjin Gun' 처리
            del split_case[10]  # 중복된 부분 제거

        return split_case

    check_table = kwargs["task_instance"].xcom_pull(task_ids=task_id, key='check_table')

    print(check_table)

    if check_table:
        print('Table is Exists')
    else:
        p: ParamsDict = kwargs["params"]
        auth_key = p["serviceKey"]
        conn_id = p['conn_id']

        params = {
            'authKey': auth_key,
            'help': 0,
            'inf': 'AWS'
        }
        url = "https://apihub.kma.go.kr/api/typ01/url/stn_inf.php?"
        columns = ["STN_ID", "LON", "LAT", "STN_SP", "HT", "HT_WD", "LAU_ID", "STN_AD", "STN_KO", "STN_EN", "FCT_ID",
                   "LAW_ID", "BASIN"]

        max_retries = 3
        delay = 5

        for attempt in range(max_retries):
            try:
                content_data = response_data(url, params)
            except RequestException as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                time.sleep(delay)

        df = pd.DataFrame([process_case(d.replace(" *", "").strip()) for d in content_data], columns=columns)

        try:
            engine = mariadb_connection(conn_id)
            session_ = sessionmaker(bind=engine)
            session = session_()

            data = df.to_dict("records")

            for n, r in enumerate(data):
                for key, value in data[n].items():
                    if isinstance(value, float) and np.isnan(value):
                        data[n][key] = None

            for d in data:
                session.add(AwsStnInfo(**d))

            session.commit()
            session.close()

        except Exception as e:
            session.rollback()
            raise IOError(f'삽입 실패! : {e}')
