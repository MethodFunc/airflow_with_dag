from __future__ import annotations

import logging
import math
from datetime import datetime
from pathlib import Path

from airflow.models.dag import DAG
from airflow.models.param import Param
# Bash
from airflow.operators.empty import EmptyOperator
# Python
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.utils.trigger_rule import TriggerRule

from aws_bins import kma_api_data
from aws_bins.CRUD import checking_stn_id, insert_data
from database.connection import mariadb_connection
from airflow.models.param import ParamsDict

log = logging.getLogger(__name__)

target_stn = [712, 174]


def preprocessing(group_id, task_id, stn, **kwargs):
    """
    기상청의 aws api들은 -50 아래는 대부분 결측 값 또는 이상 값임
    :param group_id:
    :param task_id:
    :param stn:
    :param kwargs:
    :return:
    """
    dataframe = kwargs['ti'].xcom_pull(task_ids=f'{group_id}.{task_id}_{stn}', key=f'{stn}_data')
    for col in dataframe.columns[2:]:
        dataframe[col] = dataframe[col].astype(float)
        dataframe[col] = dataframe[col].apply(lambda x: math.nan if x <= -50 else x)

    kwargs['ti'].xcom_push(key=f"{stn}_data", value=dataframe)


def create_tables(**kwargs):
    """
    아직 작동 안됨. 고칠 예정
    :param conn_id:
    :return:
    """
    from sqlalchemy.orm import declarative_base
    p: ParamsDict = kwargs["params"]
    conn_id = p["conn_id"]

    engine = mariadb_connection(conn_id)
    base = declarative_base()
    base.metadata.create_all(engine)


with DAG(
        dag_id=Path(__file__).stem,
        dag_display_name="AWS API 수집기",
        schedule=None,
        # 스케줄러 설정 시 파라미터의 default를 지정해줘야함
        # schedule="@hourly",
        start_date=datetime(2024, 9, 20),
        catchup=False,
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
    start = EmptyOperator(task_id='start', task_display_name="시작")
    end = EmptyOperator(task_id='end', trigger_rule=TriggerRule.NONE_FAILED, task_display_name="종료")

    check_stn_list = []
    aws_data_list = []

    stn_check_group = TaskGroup(group_id='stn_check', tooltip='지점 존재 확인')

    aws_group = TaskGroup(group_id='aws_group', tooltip='방재기상관측 데이터 수집')
    cloud_group = TaskGroup(group_id='cloud_group', tooltip="운고 운량 데이터 수집")
    visible_group = TaskGroup(group_id='visible_group', tooltip="시정 데이터 수집")
    temperature_group = TaskGroup(group_id='temperature_group', tooltip='온도 데이터 수집')
    pre_group = TaskGroup(group_id='Preprocessing_group', tooltip='전처리')
    insert_group = TaskGroup(group_id='Insert_group', tooltip='데이터베이스 삽입 처리')

    crt_table = PythonOperator(
        task_id='crt_table',
        task_display_name='테이블 생성',
        python_callable=create_tables,
    )

    start >> crt_table >> end

    for stn in target_stn:
        stn = str(stn)
        check_stn = PythonOperator(
            task_id=f'check_stns_{stn}',
            task_display_name=f'{stn}_지점 번호 확인',
            python_callable=checking_stn_id,
            op_kwargs={'stn': stn},
            trigger_rule=TriggerRule.ALL_SUCCESS,
            task_group=stn_check_group
        )
        aws_task = PythonOperator(
            task_id=f'aws_data_{stn}',
            task_display_name=f'{stn} 데이터 가져오기',
            python_callable=kma_api_data,
            provide_context=True,
            op_kwargs={"stn": stn, 'kind': 'aws'},
            trigger_rule=TriggerRule.ALL_SUCCESS,
            task_group=aws_group,
        )
        visible_task = PythonOperator(
            task_id=f'aws_visible_{stn}',
            task_display_name=f'{stn} 시정 데이터 가져오기',
            python_callable=kma_api_data,
            provide_context=True,
            op_kwargs={"stn": stn, 'kind': 'visible'},
            trigger_rule=TriggerRule.ALL_SUCCESS,
            task_group=visible_group,
        )

        cloud_task = PythonOperator(
            task_id=f'aws_cloud_{stn}',
            task_display_name=f'{stn} 운량 데이터 가져오기',
            python_callable=kma_api_data,
            provide_context=True,
            op_kwargs={"stn": stn, 'kind': 'cloud'},
            trigger_rule=TriggerRule.ALL_SUCCESS,
            task_group=cloud_group,
        )

        temperature_task = PythonOperator(
            task_id=f'aws_temperature_{stn}',
            task_display_name=f'{stn} 온도 데이터 가져오기',
            python_callable=kma_api_data,
            provide_context=True,
            op_kwargs={"stn": stn, 'kind': 'temperature'},
            trigger_rule=TriggerRule.ALL_SUCCESS,
            task_group=temperature_group,
        )

        aws_pre = PythonOperator(
            task_id=f"aws_pre_{stn}",
            task_display_name=f'{stn} aws 데이터 전처리',
            python_callable=preprocessing,
            provide_context=True,
            op_args=['aws_group', 'aws_data', stn],
            trigger_rule=TriggerRule.ALL_DONE,
            task_group=pre_group

        )

        temp_pre = PythonOperator(
            task_id=f"temperature_pre_{stn}",
            task_display_name=f'{stn} 온도 전처리',
            python_callable=preprocessing,
            provide_context=True,
            op_args=['temperature_group', 'aws_temperature', stn],
            trigger_rule=TriggerRule.ALL_DONE,
            task_group=pre_group

        )

        vis_pre = PythonOperator(
            task_id=f"visible_pre_{stn}",
            task_display_name=f'{stn} 시정 자료 전처리',
            python_callable=preprocessing,
            provide_context=True,
            op_args=['visible_group', 'aws_visible', stn],
            trigger_rule=TriggerRule.ALL_DONE,
            task_group=pre_group

        )

        ins_aws = PythonOperator(
            task_id=f'aws_insert_data_{stn}',
            task_display_name=f'{stn} AWS 삽입',
            python_callable=insert_data,
            provide_context=True,
            op_kwargs={

                'group_id': 'Preprocessing_group',
                'task_id': f"aws_pre_{stn}",
                'stn': stn
            },
            trigger_rule=TriggerRule.ALL_DONE,
            task_group=insert_group
        )
        ins_cloud = PythonOperator(
            task_id=f'cloud_insert_data_{stn}',
            task_display_name=f'{stn} 운량 삽입',
            python_callable=insert_data,
            provide_context=True,
            op_kwargs={

                'group_id': 'cloud_group',
                'task_id': f"aws_cloud_{stn}",
                'stn': stn
            },
            trigger_rule=TriggerRule.ALL_DONE,
            task_group=insert_group
        )
        ins_temp = PythonOperator(
            task_id=f'visible_insert_data_{stn}',
            task_display_name=f'{stn} 시정 삽입',
            python_callable=insert_data,
            provide_context=True,
            op_kwargs={

                'group_id': 'Preprocessing_group',
                'task_id': f"visible_pre_{stn}",
                'stn': stn
            },
            trigger_rule=TriggerRule.ALL_DONE,
            task_group=insert_group
        )

        ins_vis = PythonOperator(
            task_id=f'temperature_insert_data_{stn}',
            task_display_name=f'{stn} 온도 삽입',
            python_callable=insert_data,
            provide_context=True,
            op_kwargs={

                'group_id': 'Preprocessing_group',
                'task_id': f"temperature_pre_{stn}",
                'stn': stn
            },
            trigger_rule=TriggerRule.ALL_DONE,
            task_group=insert_group
        )

        start >> check_stn >> [aws_task, cloud_task, temperature_task, visible_task] >> end
        aws_group >> aws_pre >> ins_aws
        temperature_group >> temp_pre >> ins_temp
        visible_group >> vis_pre >> ins_vis
        cloud_group >> ins_cloud
        insert_group >> end
