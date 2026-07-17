#!/bin/bash

export AIRFLOW_HOME="$(pwd)/airflow_home"
export AIRFLOW__CORE__DAGS_FOLDER="$(pwd)/src"
export AIRFLOW__CORE__LOAD_EXAMPLES=False

airflow standalone