from flask import Flask, jsonify
from celery import Celery

app = Flask(__name__)
app.config["CELERY_BROKER_URL"] = "redis://localhost:6379/0"

celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)
celery.conf.result_backend_transport_options = {
    'global_keyprefix': 'celery_'
}

@celery.task()
def add(x, y):
        return x + y

@celery.task()
def error():
    raise BufferError("Fake buffer error! Bleh!")

@app.route('/')
def add_task():
    for i in range(10_000):
        add.delay(i, i)
    return jsonify({'status': 'ok'})

@app.route('/error')
def error_task():
    for i in range(3):
        error.delay()
    return jsonify({'status': 'error'})