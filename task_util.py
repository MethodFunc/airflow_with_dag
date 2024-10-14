from airflow.utils.task_group import TaskGroup
from airflow.operators.python import PythonOperator
from aws_bins import kma_api_data, preprocessing
from database import insert_data
from database.CRUD import create_tables


def get_create_table_operator(kind='aws', task_id='crt_table', **kwargs):
    """
    PythonOperator를 반환하는 팩토리 함수
    """
    return PythonOperator(
        task_id=f'{kind}_{task_id}',
        python_callable=create_tables,
        op_kwargs={'kind': kind},
        provide_context=True,
        **kwargs
    )


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
