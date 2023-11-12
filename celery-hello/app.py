from celery import Celery

app = Celery('hello', broker='redis://localhost:6379/0')
app.conf.result_backend_transport_options = {
    'global_keyprefix': 'celery_'
}

@app.task
def hello():
    return 'hello world'

if __name__ == '__main__':
    args = ['worker', '--loglevel=INFO']
    app.worker_main(argv=args)