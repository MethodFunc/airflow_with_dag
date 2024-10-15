from datetime import datetime, timedelta

import time
import pandas as pd
import requests
from airflow.models.param import ParamsDict
from requests.exceptions import RequestException


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

    start_idx = 0
    for n, d in enumerate(data):
        if '#' in d and n - start_idx == 1:
            start_idx = n

    content_data = data[start_idx+1:-2]

    return content_data


def create_dataframe(data, columns):
    df = pd.DataFrame(data, columns=columns)
    df['CR_YMD'] = pd.to_datetime(df['CR_YMD'])
    df = df[~df['CR_YMD'].duplicated()]
    df.reset_index(inplace=True, drop=True)
    df = df.where(pd.notnull(df), None)
    return df


def kma_api_data(stn, kind: str = 'aws', **kwargs):
    max_retries = 3
    delay = 5
    column_dict = {
        'aws': ['CR_YMD', 'STN_ID', 'WD1', 'WS1', 'WDS', 'WSS', 'WD10', 'WS10', 'TA', 'RE', 'RN_15m', 'RN_60m',
                'RN_12H', 'RN_DAY', 'HM', 'PA', 'PS', 'TD'],
        'cloud': ['CR_YMD', 'STN_ID', 'LON', 'LAT', 'CH_LOW', 'CH_MID', 'CH_TOP', 'CA_TOT'],
        'temperature': ['CR_YMD', 'STN_ID', 'TA', 'HM', 'TD', 'TG', 'TS', 'TE005', 'TE01', 'TE02', 'TE03', 'TE05',
                        'TE10',
                        'TE15', 'TE30', 'TE50', 'PA', 'PS'],
        'visible': ['CR_YMD', 'STN_ID', 'LON', 'LAT', 'S', 'VIS1', 'VIS10', 'WW1', 'WW15'],
        'ww': ['CR_YMD', 'STN_ID', 'LON', 'LAT', 'S', 'N', 'WW1', 'NN1'],

        'asos': ['CR_YMD', 'STN_ID', 'WD', 'WS', 'GST_WD', 'GST_WS', 'GST_TM', 'PA', 'PS', 'PT', 'PR', 'TA', 'TD', 'HM', 'PV', 'RN',
           'RN_DAY', 'RN_JUN', 'RN_INT', 'SD_HR3', 'SD_DAY', 'SD_TOT', 'WC', 'WP', 'WW', 'CA_TOT', 'CA_MID', 'CH_MIN', 'CT',
           'CT_TOP', 'CT_MID', 'CT_LOW', 'VS', 'SS', 'SI', 'ST_GD', 'TS', 'TE_005', 'TE_01', 'TE_02', 'TE_03', 'ST_SEA', 'WH',
           'BF', 'IR', 'IX']
    }
    api_urls = {
        'aws': 'https://apihub.kma.go.kr/api/typ01/cgi-bin/url/nph-aws2_min?',
        'cloud': 'https://apihub.kma.go.kr/api/typ01/cgi-bin/url/nph-aws2_min_cloud?',
        'temperature': 'https://apihub.kma.go.kr/api/typ01/cgi-bin/url/nph-aws2_min_lst?',
        'visible': 'https://apihub.kma.go.kr/api/typ01/cgi-bin/url/nph-aws2_min_vis?',
        'ww': 'https://apihub.kma.go.kr/api/typ01/cgi-bin/url/nph-aws2_min_ww1?',
        'asos': 'https://apihub.kma.go.kr/api/typ01/url/kma_sfctm3.php?'

    }

    params = common_parma(stn, kwargs)

    if kind == 'ww':
        params.update({'itv': 1, 'range': 1})
        print(params)

    for attempt in range(max_retries):
        try:
            url = api_urls.get(kind, None)
            columns = column_dict.get(kind, None)

            if url is None:
                raise ValueError('choose asos, aws, cloud, temperature')

            content_data = response_data(url, params)
        except RequestException as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
            time.sleep(delay)
    if kind == 'asos':
        df = create_dataframe([d.strip().split() for d in content_data], columns)
    else:
        df = create_dataframe([d.replace(",=", "").split(",") for d in content_data], columns)

    print(df)

    kwargs['ti'].xcom_push(key=f"{stn}_data", value=df)
