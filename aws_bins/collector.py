from datetime import datetime, timedelta

import pandas as pd
import requests
from airflow.models.param import ParamsDict


def common_parma(stn, kwargs):
    p: ParamsDict = kwargs["params"]
    auth_key = p["serviceKey"]

    # 1. disp: 1 기준
    params = {
        'authKey': auth_key,
        'stn': stn,
        'help': 0,
        'disp': 1,
        'tm1': (datetime.now() - timedelta(hours=1)).strftime("%Y%m%d%H00"),
        'tm2': datetime.now().strftime("%Y%m%d%H00")
    }

    return params


def response_data(url, params):
    response = requests.get(url, params)
    if response.status_code == 401:
        raise ValueError("유효한 인증키가 아닙니다.")

    content = response.text

    data = content.split("\n")
    content_data = data[3:-2]

    return content_data


def create_dataframe(data, columns):
    df = pd.DataFrame([d.replace(",=", "").split(",") for d in data], columns=columns)
    df['CR_YMD'] = pd.to_datetime(df['CR_YMD'])
    df = df[~df['CR_YMD'].duplicated()]
    df.reset_index(inplace=True, drop=True)
    df = df.where(pd.notnull(df), None)
    return df


def kma_api_data(stn, kind: str = 'aws', **kwargs):
    column_dict = {
        'aws': ['CR_YMD', 'STN_ID', 'WD1', 'WS1', 'WDS', 'WSS', 'WD10', 'WS10', 'TA', 'RE', 'RN_15m', 'RN_60m',
                'RN_12H', 'RN_DAY', 'HM', 'PA', 'PS', 'TD'],
        'cloud': ['CR_YMD', 'STN_ID', 'LON', 'LAT', 'CH_LOW', 'CH_MID', 'CH_TOP', 'CA_TOT'],
        'temperature': ['CR_YMD', 'STN_ID', 'TA', 'HM', 'TD', 'TG', 'TS', 'TE005', 'TE01', 'TE02', 'TE03', 'TE05',
                        'TE10',
                        'TE15', 'TE30', 'TE50', 'PA', 'PS'],
        'visible': ['CR_YMD', 'STN_ID', 'LON', 'LAT', 'S', 'VIS1', 'VIS10', 'WW1', 'WW15']
    }
    api_urls = {
        'aws': 'https://apihub.kma.go.kr/api/typ01/cgi-bin/url/nph-aws2_min?',
        'cloud': 'https://apihub.kma.go.kr/api/typ01/cgi-bin/url/nph-aws2_min_cloud?',
        'temperature': 'https://apihub.kma.go.kr/api/typ01/cgi-bin/url/nph-aws2_min_lst?',
        'visible': 'https://apihub.kma.go.kr/api/typ01/cgi-bin/url/nph-aws2_min_vis?'

    }

    params = common_parma(stn, kwargs)

    url = api_urls.get(kind, None)
    columns = column_dict.get(kind, None)
    if url is None:
        raise ValueError('choose aws, cloud, temperature')

    content_data = response_data(url, params)
    df = create_dataframe(content_data, columns)

    print(df)

    kwargs['ti'].xcom_push(key=f"{stn}_data", value=df)
