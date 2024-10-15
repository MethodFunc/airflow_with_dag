import math
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule


def preprocessing(group_id, task_id, stn, **kwargs):
    """
    기상청의 aws api들은 -50 아래는 대부분 결측 값 또는 이상 값임
    :param task_id:
    :param stn:
    :param kwargs:
    :return:
    """
    dataframe = kwargs['ti'].xcom_pull(task_ids=f'{group_id}.{task_id}', key=f'{stn}_data')
    # dataframe = kwargs['ti'].xcom_pull(task_ids=f'{task_id}_{stn}', key=f'{stn}_data')
    print(f"Debug: {dataframe}")
    for col in dataframe.columns[2:]:
        try:
            dataframe[col] = dataframe[col].astype(float)
            dataframe[col] = dataframe[col].apply(lambda x: math.nan if x <= -50 else x)
        except ValueError:
            print(f'{col} is {type(col)}')

    kwargs['ti'].xcom_push(key=f"{stn}_data", value=dataframe)


def common_task():
    start = EmptyOperator(task_id='start', task_display_name="시작")
    end = EmptyOperator(task_id='end', trigger_rule=TriggerRule.NONE_FAILED, task_display_name="종료")

    return start, end

