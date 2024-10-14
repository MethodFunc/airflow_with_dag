FROM apache/airflow:2.10.2-python3.11
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
         vim openjdk-17-jre-headless \
  && apt-get autoremove -yqq --purge \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*
USER airflow
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" lxml
RUN pip install --no-cache-dir "apache-airflow-providers-celery" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.2/constraints-3.11.txt"
RUN pip install --no-cache-dir "apache-airflow-providers-mysql" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.2/constraints-3.11.txt"
RUN pip install --no-cache-dir "apache-airflow-providers-mongo" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.2/constraints-3.11.txt"
RUN pip install --no-cache-dir "pymongo" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.2/constraints-3.11.txt"
RUN pip install --no-cache-dir "pymysql" --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.2/constraints-3.11.txt"
RUN pip install mlflow