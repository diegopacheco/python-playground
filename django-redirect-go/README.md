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

## What about React Native?

```
> about this in test.sh (curl -L -X GET http://localhost:8000/getlast) could the client follow redirect without -L flag
 - what the client is on react native?

⏺ In React Native, HTTP clients behave differently than curl:

  React Native (fetch API)

  The fetch API in React Native follows redirects by default - you don't need any special flags.

  fetch('http://localhost:8000/getlast')
    .then(response => response.json())

  This will automatically follow the redirect without any additional configuration.

  Curl behavior

  Curl requires the -L flag to follow redirects. Without it:
  - curl http://localhost:8000/getlast - Returns the 3xx redirect response
  - curl -L http://localhost:8000/getlast - Follows the redirect and gets the final response

  Controlling redirect behavior in React Native

  If you want to change the default behavior, you can use the redirect option:

  fetch('http://localhost:8000/getlast', {
    redirect: 'manual'  // 'follow' (default), 'error', or 'manual'
  })

  Summary: React Native clients will follow redirects automatically, unlike curl which needs -L. The -L flag in test.sh
   is only necessary for the curl command to work properly.
```