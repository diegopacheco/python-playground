import time

def app(environ, start_response):
        time.sleep(2)
        data = b"Hello, World!\n"
        start_response("200 OK", [
            ("Content-Type", "text/plain"),
            ("Content-Length", str(len(data)))
         ])  
        return iter([data])