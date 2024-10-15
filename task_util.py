from airflow.utils.task_group import TaskGroup
from airflow.operators.python import PythonOperator
from aws_bins import kma_api_data, preprocessing, stn_info_data
from database import insert_data, check_and_create_table, checking_stn_id


def get_create_table_operator(kind='aws', task_id='crt_table', **kwargs):
    """
    PythonOperator를 반환하는 팩토리 함수
    """
    return PythonOperator(
        task_id=f'{kind}_{task_id}',
        python_callable=check_and_create_table,
        op_kwargs={'kind': kind},
        provide_context=True,
        **kwargs
    )


def create_info_check_group(kind, target_stn):
    def create_stn_information_group(dag):
        with TaskGroup(group_id=f'{kind}_group', tooltip=f'지점 번호 삽입') as group:
            table_exists_create = PythonOperator(
                task_id='table_exists_create',
                python_callable=check_and_create_table,
                provide_context=True,

                op_kwargs={
                    'kind': kind
                }
            )

            stn_info = PythonOperator(
                task_id='stn_data_insert',
                python_callable=stn_info_data,
                op_kwargs={
                    'kind': kind,
                    'task_id': f'{kind}_group.table_exists_create'}
            )

            table_exists_create >> stn_info

        return group

    def check_stn_info_group(dag):
        with TaskGroup(group_id=f'check_group', tooltip=f'지점 번호 확인') as group:
            for stn in target_stn:
                stn = str(stn)
                check_stn = PythonOperator(
                    task_id=f'check_stns_{stn}',
                    python_callable=checking_stn_id,
                    op_kwargs={'kind': kind, 'stn': stn},
                )

                check_stn

        return group

    if target_stn is None:
        return create_stn_information_group
    else:
        return check_stn_info_group


def create_data_collection_group(kind, target_stn):
    def data_collection_group(dag):
        with TaskGroup(group_id=f'{kind}_group', tooltip=f'{kind} 데이터 수집 및 처리') as group:
            crt_table = get_create_table_operator(kind)
            for stn in target_stn:
                stn = str(stn)

                collect_data = PythonOperator(
                    task_id=f'{kind}_data_{stn}',
                    python_callable=kma_api_data,
                    op_kwargs={"stn": stn, 'kind': kind},
                )

                preprocess_data = PythonOperator(
                    task_id=f"{kind}_pre_{stn}",
                    python_callable=preprocessing,
                    op_kwargs={'group_id': f'{kind}_group', 'task_id': f"{kind}_data_{stn}", 'stn': stn},
                )

                insert_data_task = PythonOperator(
                    task_id=f'{kind}_insert_data_{stn}',
                    python_callable=insert_data,
                    op_kwargs={
                        'kind': kind,
                        'group_id': f'{kind}_group',
                        'task_id': f"{kind}_pre_{stn}",
                        'stn': stn
                    },
                )

                crt_table >> collect_data >> preprocess_data >> insert_data_task

        return group

    return data_collection_group
