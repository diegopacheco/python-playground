from flask import Flask
from celery import Celery
from prometheus_client import start_http_server, Counter
import time
import threading

app = Flask(__name__)

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['result_backend'],
        broker=app.config['broker_url']
    )
    celery.conf.update(app.config)
    return celery

app.config.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0'
)

celery_app = make_celery(app)

REQUEST_COUNT = Counter('request_count', 'Total number of requests')

@celery_app.task
def add(x, y):
    return x + y

@celery_app.task
def sleep_task():
    time.sleep(3)
    return 'Slept for 3 seconds'

@app.route('/')
def hello():
    REQUEST_COUNT.inc()
    return 'Hello, World!'

@app.route('/add/<int:a>/<int:b>')
def add_route(a, b):
    REQUEST_COUNT.inc()
    result = add.delay(a, b)
    return f'Task submitted: {result.id}'

@app.route('/sleep')
def sleep_route():
    REQUEST_COUNT.inc()
    result = sleep_task.delay()
    return f'Sleep task submitted: {result.id}'

def start_prometheus_server():
    try:
        start_http_server(9000)
    except OSError as e:
        if e.errno == 98:
            print('Prometheus client already running, ignoring...')
        else:
            raise

threading.Thread(target=start_prometheus_server).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)