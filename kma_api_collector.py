from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from airflow.models.dag import DAG
from airflow.models.param import Param
from functools import partial

from task_util import create_data_collection_group, create_info_check_group
from aws_bins import common_task
from airflow.models.baseoperator import cross_downstream

log = logging.getLogger(__name__)

target_stn = [712, 174]

with DAG(
        dag_id=Path(__file__).stem,
        dag_display_name="AWS API 수집기",
        schedule="3 * * * *",
        start_date=datetime(2024, 9, 20),
        catchup=False,
        max_active_runs=1,
        concurrency=1,
        tags=["AWS", "기상청", "지역별상세관측자료", "방재기상관측"],
        params={
            "serviceKey": Param(
                # 스케줄러 시 api 키 적기
                # default="your_api_key",
                type="string",
                title="api key",
                description="API키를 입력해주세요. 발급은 https://apihub.kma.go.kr/ 회원가입 후 가능합니다.",
            ),
            "conn_id": Param(
                # 스케줄러 시 데이터베이스 명 적기
                # default='maria_database',
                type="string",
                title="conn_id",
                description="airflow에 등록한 마리아 데이터베이스의 conn_id를 입력해주세요.",
            ),
        },
        default_args={
            'owner': 'methodfunc'
        }
) as dag:
    start, end = common_task()
    start, end = common_task()
    stn_info_group = create_info_check_group('aws_info', None)(dag)
    check_stn_group = create_info_check_group('aws_info', target_stn)(dag)

    collector = partial(create_data_collection_group, target_stn=target_stn)
    aws_group = collector('aws')(dag)
    cloud_group = collector('cloud')(dag)
    visible_group = collector('visible')(dag)
    temperature_group = collector('temperature')(dag)
    ww_group = collector('ww')(dag)

    start >> stn_info_group >> check_stn_group
    cross_downstream(check_stn_group, [aws_group, cloud_group])
    cross_downstream([aws_group, cloud_group], [visible_group, temperature_group])
    [visible_group, temperature_group] >> ww_group >> end
