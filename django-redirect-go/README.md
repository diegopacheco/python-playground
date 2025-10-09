# Redirect

Imagine you have code in Python(endpoints) that you want to migrate to go. <br/>
So you keep exact the same contract, the endpoint is the same but you move than to Go. <br/>
Them in Python you do a redict, that way the client does not need to update the endpoint immediately, this is useful when you have a lot of clients and you want to give them time to update their code or in mobile apps that people dont update the app. <br/>

## Components

* Django Rest Framework
* Go (Gin)
* Postgres (schenma: `go_schema` and schema: `django_schema`)
* Podman-Compose

## Result

```bash
❯ ./test.sh
Testing Django app (port 8000)...
{"id": 3, "number": 42, "date": "2025-10-08"}
{"records": [{"id": 1, "number": 42, "date": "2025-10-08"}, {"id": 2, "number": 42, "date": "2025-10-08"}, {"id": 3, "number": 42, "date": "2025-10-08"}]}

Testing Go app (port 8001)...
{"id": 3, "number": 42, "date": "2025-10-08"}
{"records": [{"id": 1, "number": 42, "date": "2025-10-08"},{"id": 2, "number": 42, "date": "2025-10-08"},{"id": 3, "number": 42, "date": "2025-10-08"}]}

Testing /getlast endpoint...
Django (redirects to Go):
{"id": 3, "number": 42, "date": "2025-10-08"}
Go (direct):
{"id": 3, "number": 42, "date": "2025-10-08"}
```
