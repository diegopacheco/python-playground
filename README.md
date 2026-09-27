# python-playground

python-playground: POCs with Python. Every project lives in its own folder, most have a `run.sh` and many have their own README.

## 🐍 Python Essentials

Small, focused projects on one library or one language feature each.
Each one has its own README and runs on its own.

* [python-essentials-basics](python-essentials-basics/) - `for`, `while`, collections, `lambda`, `sorted` with keys and classes with inheritance
* [python-essentials-idiomatic](python-essentials-idiomatic/) - Comprehensions, `enumerate`/`zip`, unpacking, `dict.get`/`setdefault` and EAFP
* [python-essentials-hidden-gems](python-essentials-hidden-gems/) - `for/else`, walrus, dict merge `|`, f-string `=` and `collections`/`itertools`
* [python-essentials-functional](python-essentials-functional/) - `map`, `filter`, `reduce`, closures, `functools.partial` and composition
* [python-essentials-slices](python-essentials-slices/) - Ranges, steps, negative indexes, reversing, slice assignment and `slice`
* [python-essentials-types](python-essentials-types/) - Type hints, `TypedDict`, `NewType`, `Protocol` and a `Generic` class
* [python-essentials-threads](python-essentials-threads/) - `Thread`, `Lock`, `ThreadPoolExecutor`, results through a `Queue` and daemon threads
* [python-essentials-semaphores](python-essentials-semaphores/) - `Semaphore` and `BoundedSemaphore` to cap concurrency
* [python-essentials-json](python-essentials-json/) - `dumps`/`loads`, pretty printing, a custom encoder and type mapping
* [python-essentials-jwt](python-essentials-jwt/) - JWT HS256 with only `hmac`, `hashlib`, `base64` and `json`
* [python-essentials-pii-aes](python-essentials-pii-aes/) - Encrypt PII with AES-256-GCM using `cryptography`
* [python-essentials-bleach](python-essentials-bleach/) - Sanitize untrusted HTML and stop XSS with `bleach`
* [python-essentials-requests](python-essentials-requests/) - Query params, JSON bodies, headers, status handling and a reused `Session`
* [python-essentials-pydantic](python-essentials-pydantic/) - Pydantic v2 models, constraints, validators and nested models
* [python-essentials-sqlalchemy](python-essentials-sqlalchemy/) - SQLAlchemy 2.0 ORM over in-memory SQLite with relationships and joins
* [python-essentials-sqlalchemy-postgres-rest](python-essentials-sqlalchemy-postgres-rest/) - FastAPI + SQLAlchemy 2.0 + PostgreSQL REST API with Swagger UI
* [python-essentials-postgres-pool](python-essentials-postgres-pool/) - PostgreSQL pooling with `psycopg2` `ThreadedConnectionPool`
* [python-essentials-mysql-pool](python-essentials-mysql-pool/) - MySQL pooling with `mysql-connector-python`
* [python-essentials-pgvector](python-essentials-pgvector/) - Vector similarity search inside PostgreSQL with `pgvector`
* [python-essentials-flask-rest](python-essentials-flask-rest/) - Flask REST API with every HTTP verb over an in-memory book store
* [python-essentials-django](python-essentials-django/) - Django settings, routing and JSON views in a single file
* [python-essentials-streamlit](python-essentials-streamlit/) - Streamlit app with input, slider, live table and line chart
* [python-essentials-airflow](python-essentials-airflow/) - Airflow ETL DAG `extract >> transform >> load` with XCom
* [python-essentials-temporal](python-essentials-temporal/) - Temporal workflow with two activities on a local Temporal server
* [python-essentials-ollama](python-essentials-ollama/) - Local Llama with the `ollama` client: chat, streaming and embeddings
* [python-essentials-llamaindex](python-essentials-llamaindex/) - Fully local RAG pipeline with LlamaIndex
* [python-essentials-rake-nltk](python-essentials-rake-nltk/) - Keyword extraction with RAKE on top of NLTK
* [python-essentials-fire](python-essentials-fire/) - Turn a class into a CLI with `python-fire`
* [python-essentials-rich](python-essentials-rich/) - Panels, colored tables, markup and rules with `rich`
* [python-essentials-tqdm](python-essentials-tqdm/) - Progress bars for loops with `tqdm`
* [python-essentials-distro](python-essentials-distro/) - Detect the OS distribution with `distro`
* [python-essentials-pylint](python-essentials-pylint/) - Fully typed code linted by `pylint` to 10.00/10
* [python-essentials-pyproject](python-essentials-pyproject/) - A package defined only by `pyproject.toml` with a console script

## 🧬 Language Features

How the language itself works: data model, dunder methods, scoping and syntax.
Each one is a few lines of code that show one idea.

* [bag-of-cats](bag-of-cats/) - Basics, control flow, dicts and lists
* [basic-lang-fun](basic-lang-fun/) - Dicts, functions, if/else, iterators and list comprehensions
* [python-cool-stuff](python-cool-stuff/) - Short idioms: reverse slices, in-place swaps and more
* [any-and-all](any-and-all/) - `any()` and `all()` over generators
* [walrus-operator](walrus-operator/) - The `:=` assignment expression
* [f-string-expressions](f-string-expressions/) - Expressions inside f-strings
* [match-stmt](match-stmt/) - The `match` statement
* [structural-pattern-matcher](structural-pattern-matcher/) - Structural pattern matching on shapes of data
* [umpacking](umpacking/) - Star unpacking: `first, *middle, last`
* [print-array](print-array/) - Print a list with the `*` operator
* [slice-assign](slice-assign/) - Replace parts of a list with slice assignment
* [set-ops](set-ops/) - Union, intersection and difference on sets
* [frozen-set-immutable-sets](frozen-set-immutable-sets/) - Immutable sets with `frozenset`
* [dictionary-meerge](dictionary-meerge/) - Merging dictionaries
* [dict-has-key-fun](dict-has-key-fun/) - Checking keys in a dict
* [magic-dict](magic-dict/) - A dict-like class with `__missing__`, `__bool__` and other dunders
* [iterator](iterator/) - Custom iterators with `__iter__` and `__next__`
* [sequence-protocol](sequence-protocol/) - Implementing the sequence protocol
* [comparisons](comparisons/) - Rich comparison methods on a `Version` class
* [overloading-operators](overloading-operators/) - Operator overloading with dunder methods
* [reflected-arithmetic-operators](reflected-arithmetic-operators/) - Reflected operators like `__radd__`
* [context-manager](context-manager/) - `with` blocks and custom context managers
* [property-decorators](property-decorators/) - `@property`, setters and deleters
* [cached-properties](cached-properties/) - `functools.cached_property`
* [get-atributte-protections](get-atributte-protections/) - Protecting attributes with `__getattribute__`
* [data-class](data-class/) - `@dataclass`
* [abstract-base-class](abstract-base-class/) - `abc.ABC` and `@abstractmethod`
* [mixins](mixins/) - Composing behavior with mixin classes
* [meta-classes](meta-classes/) - Metaclasses
* [dynamic-class-creation](dynamic-class-creation/) - Building classes at runtime with `type()`
* [singleton-annotation-fun](singleton-annotation-fun/) - A singleton decorator
* [proxy](proxy/) - A lazy module proxy with `__getattr__`
* [method-polymorphism-simple](method-polymorphism-simple/) - Method polymorphism
* [single-dispatch](single-dispatch/) - `functools.singledispatch`
* [python-multipledispatch-simple](python-multipledispatch-simple/) - Multiple dispatch with `multipledispatch`
* [decorator-but-i-will-call-annotations](decorator-but-i-will-call-annotations/) - Decorators
* [decorator-but-i-will-call-annotations-two](decorator-but-i-will-call-annotations-two/) - More decorators
* [fp-partial-functions](fp-partial-functions/) - `functools.partial`
* [lru-cache](lru-cache/) - `functools.lru_cache`
* [coroutine-send](coroutine-send/) - Generator coroutines driven with `send()`
* [namespace-globals](namespace-globals/) - Global and local namespaces
* [dynamic-namespace](dynamic-namespace/) - Namespaces built at runtime
* [namespace-packages](namespace-packages/) - Namespace packages without `__init__.py`
* [deep-shallow-object-copy](deep-shallow-object-copy/) - `copy.copy` vs `copy.deepcopy`
* [weak-references](weak-references/) - `weakref`
* [pickle-serialization](pickle-serialization/) - Serialization with `pickle`
* [simple-execptiondict-fun](simple-execptiondict-fun/) - Exceptions and dicts
* [coded](coded/) - A custom codec registered with `codecs`
* [dis](dis/) - Reading bytecode with `dis`
* [inspect-fun](inspect-fun/) - Runtime introspection with `inspect`
* [memory-mgmt-fun-test](memory-mgmt-fun-test/) - Memory management
* [pyothon-hell-on-pointers-fun](pyothon-hell-on-pointers-fun/) - C-style pointers in Python with `pointers.py`
* [fizz-buzz-noif](fizz-buzz-noif/) - FizzBuzz without `if`
* [regular-expressions-fun](regular-expressions-fun/) - Regular expressions with `re`
* [python-multiline-replacement-regex-fun](python-multiline-replacement-regex-fun/) - Multiline regex replacements
* [basic-date-time](basic-date-time/) - Dates and hours
* [files-fun](files-fun/) - Reading and writing files
* [json-fun](json-fun/) - JSON with the standard library

## 🔒 Typing & Code Quality

Static type checkers, linters and tooling that catch bugs before the code runs.

* [python-3-mypy](python-3-mypy/) - `mypy --strict`, mypyc compiled modules, ruff, SQLAlchemy, Alembic and Pydantic
* [python-3-ty](python-3-ty/) - Astral `ty` + ruff with SQLAlchemy, SQLite, Alembic and Pydantic on Python 3.14
* [python-3-pythonic-deck](python-3-pythonic-deck/) - A card deck on the sequence protocol, checked by `pyright` strict
* [type-hints-generics](type-hints-generics/) - Generics in type hints
* [mypy-simple-fun](mypy-simple-fun/) - mypy basics
* [pre-commit-fun](pre-commit-fun/) - pre-commit hooks
* [pdoc-fun](pdoc-fun/) - API docs generated with `pdoc`

## 🧪 Testing

Test runners and tools that make tests faster and deterministic.

* [python-uv-worksteal](python-uv-worksteal/) - pytest-xdist `--dist worksteal` under uv, with proof that stealing happens
* [VCR.py-poc](VCR.py-poc/) - Record and replay HTTP calls in tests with VCR.py
* [test-python](test-python/) - `unittest` basics

## ⚡ Concurrency & Async

Threads, processes, event loops and queues.

* [async-io-fun](async-io-fun/) - `asyncio` basics
* [uvloop_fun](uvloop_fun/) - A faster event loop with `uvloop`
* [daemon-thread-python-fun](daemon-thread-python-fun/) - Daemon threads
* [producer-consumer-queue-fun](producer-consumer-queue-fun/) - Producer and consumer over a queue
* [os-process-call](os-process-call/) - Calling OS processes
* [python-linux](python-linux/) - OS calls on Linux
* [twisted-fun](twisted-fun/) - Twisted networking
* [cyclone](cyclone/) - Cyclone web server on Twisted

## 🌐 Web Frameworks & APIs

HTTP servers, REST APIs and HTTP clients.

* [django-6-async](django-6-async/) - Async retail-banking app on Django 6
* [django](django/) - Django project
* [django-hello-world](django-hello-world/) - Django hello world
* [django-uv](django-uv/) - Django managed with uv
* [django-silk-fun](django-silk-fun/) - Profiling Django with Silk
* [django-redirect-go](django-redirect-go/) - Redirect Django endpoints to Go during a migration
* [mysite_list_apis](mysite_list_apis/) - List every Django URL with django-extensions
* [fastapi-fun](fastapi-fun/) - FastAPI basics
* [fastapi-python](fastapi-python/) - FastAPI service with tests
* [python-request-state](python-request-state/) - Async FastAPI + SQLite CRUD using request state
* [Flask-API-fun](Flask-API-fun/) - Flask API
* [hyper-flask-fun](hyper-flask-fun/) - Flask served by Hypercorn
* [fastHTML](fastHTML/) - Web UI with FastHTML
* [gunicorn-simple](gunicorn-simple/) - Gunicorn basics
* [gunicorn-playground](gunicorn-playground/) - Gunicorn + Flask + Celery with Prometheus and Grafana
* [web-hook-svr-client-poc](web-hook-svr-client-poc/) - Signed webhooks between a server and a client
* [stainless-poc](stainless-poc/) - Generate a Python SDK from OpenAPI with Stainless
* [httpx-fun](httpx-fun/) - HTTP client with `httpx`
* [python3-httpx2](python3-httpx2/) - HTTPX2 2.12 on Python 3.14
* [PyBreaker-Fun](PyBreaker-Fun/) - Circuit breaker with PyBreaker
* [xpath-python-fun](xpath-python-fun/) - XPath queries over HTML and XML
* [certificate-requests](certificate-requests/) - HTTPS requests with client certificates

## 🗄️ Databases & ORMs

Relational, key-value and document stores, with migrations and transactions.

* [Alembic-migrations](Alembic-migrations/) - Alembic schema migrations on PostgreSQL 17
* [sql-achemy-tx-magement](sql-achemy-tx-magement/) - Transaction boundary as a single decorator with SQLAlchemy
* [sql-alchemy-postgres-jsonb](sql-alchemy-postgres-jsonb/) - JSON documents in a PostgreSQL `JSONB` column with a web console
* [postgres-gin-index-poc](postgres-gin-index-poc/) - JSONB queries with and without a GIN index
* [sql-lite-web-fun](sql-lite-web-fun/) - Browse SQLite with sqlite-web
* [pickledb-fun](pickledb-fun/) - Key-value store with pickleDB
* [redis](redis/) - Redis with `redis-py`
* [memcached](memcached/) - Memcached client
* [fleetdb](fleetdb/) - FleetDB client
* [bigchaindb](bigchaindb/) - BigchainDB client
* [ids-config-bench](ids-config-bench/) - Checking 10k IDs loaded from config

## 📨 Messaging & Workflows

Queues, brokers, task runners and orchestrators.

* [celery-hello](celery-hello/) - Celery worker hello world
* [celery-flower](celery-flower/) - Celery monitored with Flower
* [python-pika-rabbitmq-simple](python-pika-rabbitmq-simple/) - RabbitMQ with Pika and metrics
* [message-sucker](message-sucker/) - Consume ActiveMQ messages over STOMP
* [zmq](zmq/) - ZeroMQ client and server
* [boto-sns-fun](boto-sns-fun/) - AWS SNS with boto
* [airflow](airflow/) - Apache Airflow
* [dagster-fun](dagster-fun/) - Dagster
* [dbt-fun](dbt-fun/) - dbt

## 📊 Data & Science

Dataframes, numerical computing, optimization and charts.

* [pandas-fun](pandas-fun/) - pandas and plotting
* [polars-fun](polars-fun/) - Polars dataframes
* [numpy-fun](numpy-fun/) - NumPy
* [scipy-fun](scipy-fun/) - SciPy graphs
* [scipy-ml-linear-regression](scipy-ml-linear-regression/) - Linear regression with SciPy
* [linear-programing-fun](linear-programing-fun/) - Bin packing, knapsack and farmer problems with linear programming
* [split-csv](split-csv/) - Split a CSV file
* [folium-fun](folium-fun/) - Maps with Folium
* [diagrams](diagrams/) - Architecture diagrams as code
* [ramdon-numbers](ramdon-numbers/) - Random numbers

## 🤖 AI & ML

Models, classifiers, computer vision and LLM tooling.

* [onmx-classifier](onmx-classifier/) - LLM model router driven by an ONNX text classifier
* [claude-code-python](claude-code-python/) - A tiny coding agent with file tools in Python
* [deep-face](deep-face/) - Face analysis with DeepFace
* [tesseract](tesseract/) - OCR with Tesseract
* [videohash-fun](videohash-fun/) - Perceptual video hashing
* [python3-posthog-fun](python3-posthog-fun/) - DVD rental API that sends product metrics to PostHog

## 🎮 Games & UI

Games, terminal effects and desktop apps.

* [tetris](tetris/) - Tetris
* [space-invaders-game](space-invaders-game/) - Space Invaders
* [pygame-snake](pygame-snake/) - Snake with pygame
* [bouncing-ball](bouncing-ball/) - Bouncing ball
* [qrcode-image-fun-poc](qrcode-image-fun-poc/) - QR Page Capture app
* [terminaltexteffects-fun](terminaltexteffects-fun/) - Terminal text effects
* [tqdm](tqdm/) - Progress bars with `tqdm`

## 🛠️ Tools & Misc

Scripts, packaging, security and one-off utilities.

* [auto-commit](auto-commit/) - Auto commit script with cron on macOS
* [download-all-my-gists-github](download-all-my-gists-github/) - Download every gist from GitHub
* [python-eggs](python-eggs/) - Packaging with eggs
* [python-call-zig-fun](python-call-zig-fun/) - Call a Zig shared library from Python
* [aes-encryption-fun](aes-encryption-fun/) - AES encryption
* [camelcase-fun](camelcase-fun/) - camelCase conversion
* [python-box](python-box/) - Dot access dicts with python-box
* [template-engine](template-engine/) - A tiny template engine with regex
* [dumb-virtual-fs](dumb-virtual-fs/) - An in-memory virtual file system
* [misc](misc/) - Evernote, Google Docs, GitHub and Google Charts API scripts

## 📘 Extras

* [python-crash-course.html](python-crash-course.html) - Python crash course
* [create-python3-project.sh](create-python3-project.sh) - Scaffold a new Python 3 project
