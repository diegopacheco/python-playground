# python-essentials-airflow

An Airflow ETL DAG with three `PythonOperator` tasks wired `extract >> transform >> load`, passing data between tasks with XCom.

### How it works

`src/dag.py` defines `extract` (pushes numbers), `transform` (squares them), and `load` (sums and prints them). Task dependencies are declared with `>>`. `run.sh` points Airflow at `src/` as its DAGs folder and starts `airflow standalone`.

### Install

```bash
./install-deps.sh
```

### Run

```bash
./run.sh
```

Open `http://localhost:8080`, log in with the credentials printed in the console, and trigger `python_essentials_etl`.

### Output

The `load` task logs:

```
loaded squares: [1, 4, 9, 16, 25] total=55
```
