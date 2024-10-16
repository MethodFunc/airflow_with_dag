# Airflow kma 기상청 api aws/asos 수집

## Description.
1. stn_check 부분은 선행으로 먼저 데이터베이스에 넣어주셔야합니다.
2. 수집은 AWS, 운량, 시정자료, 온도자료, 현천자료 총 5가지를 수집합니다.
3. https://apihub.kma.go.kr/ 해당 사이트를 가입 후 api를 발급 받아야합니다.


## Docker-compose 수정
1. AIRFLOW__CORE__FERNET_KEY 및 AIRFLOW__WEBSERVER__SECRET_KEY 키 값
```python
from cryptography.fernet import Fernet
fernet_key = Fernet.generate_key()
print(fernet_key.decode())
```
2. AIRFLOW__DATABASE__SQL_ALCHEMY_CONN 설정
```text
postgresql
postgresql+psycopg2://airflow:airflow@postgres/airflow

mariadb
mysql+pymysql://user:pwd@host:port/airflow
```

3. AIRFLOW__CELERY__RESULT_BACKEND 설정
```text
postgresql
db+postgresql://airflow:airflow@postgres/airflow

mariadb
db+mysql://user:pwd@host:port/airflow

config/airflow.cfg 의 다음 항목도 같이 수정
result_backend = ...
```

## 변경점
1. 데이터베이스가 한번에 생성되는 문제 해결
2. ASOS (종관기상관측) 스키마 추가
3. ASOS 관련 코드 업데이트
4. API의 전처리 코드 개선
5. 중복 테스크 task_util로 통합
6. catchup을 위한 시간 데이터를 task 시작 시간으로 지정 (airflow kwargs 이용)
7. 한번에 여러개의 실행을 막기 위해 catchup의 max_active_run과 concurrency 추가
8. 데드락을 처리하기 위한 sqlalchemy 설정 추가

##  트리거 화면
### 구버전
![img_1.png](img_1.png)
### 신버전
![img_5.png](img_5.png)

------

## Flow chart
### 구버전
![img.png](img.png)
### 신버전
![img_3.png](img_3.png)


![img_4.png](img_4.png)

------

## 개선점 및 문제점
connection을 param에 넣어서 유동적으로 넣을수 있도록 함 (conn_id 지정 완료)

AWS의 지점 번호도 자동으로 수집하여 데이터베이스에 삽입함. (테이블이 있을 시 삽입 안함)

데이터베이스 삽입코드에 중복처리는 있긴하지만, Celery를 도입하여 중복 실행을 막아야함. (Celery 도입)

아쉽게도 지점번호는 동적으로 넣을 수 없음. (직접 수정해야함)

스케줄러 시 파라미터는 고정해야 함.

airflow에서 지원하는 도커파일은 기본적으로 celery execute지만 worker를 여러개 만들 경우 수정이 약간 필요함.

- web server의 secret키를 적용하여 log를 볼 수 있게 해야함
- 무작정 워커를 늘리기만 하면 구동이 안 될 수 있음
- AIRFLOW__CORE__STORE_DAG_CODE: 'True' 과 AIRFLOW__CORE__STORE_SERIALIZED_DAGS: 'True' 2.0에서 지원하지만 작동이 안되서 직접 dags폴더를 worker들에게 마운트해야함

한번에 많은 api를 수집 시 무작위로 한 곳에서 failed가 생김. 이를 해결하기 위해선 한번에 수행하는 양을 줄이며 연속적으로 수행하는 거임

지점번호가 3개 이상일 경우 아래 사진과 같이 running에서 멈추는 오류가 있음. 사양이 높아 워커를 여러개 사용하지 아니하다면 지점번호는 **2**개를 권장함.
(m1 max 16gb 사양에선 worker가 2개로 구동할 수 있음 (각 worker 램 제한 2기가))

![img_6.png](img_6.png)

**현재 dag는 현재시간을 기준으로 하며, catchup을 True로 하여도 지나간 데이터는 수집하지 않음**


## Flower
![img_2.png](img_2.png)

## 도커 파일 사용 방법
1. flower 구동
docker compose --profile flower up -d
2. 도커 종료
docker compose --profile flower down
3. flower 미 구동
docker compose up -d
2. 도커 종료
docker compose down
