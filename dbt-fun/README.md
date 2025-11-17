### Intall dependencies

```bash
./install-deps.sh
```

### Run

```bash
./start.sh
```
```
❯ ./start.sh
b5c18148128e786893eed449c6f50176a9a83f3df6ce49424878cb5c881b27c7
3a8c3ff8c0e82c018182e8f21067716050564ad4f24449ee5fd684eebdb73294
dbt_postgres
Waiting for PostgreSQL to be ready...
PostgreSQL is ready
```

```bash
./run.sh
```
```
❯ ./run.sh

[notice] A new release of pip is available: 25.2 -> 25.3
[notice] To update, run: /Library/Developer/CommandLineTools/usr/bin/python3 -m pip install --upgrade pip
/Users/diegopacheco/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/runpy.py:127: RuntimeWarning: 'dbt.cli.main' found in sys.modules after import of package 'dbt.cli', but prior to execution of 'dbt.cli.main'; this may result in unpredictable behaviour
  warn(RuntimeWarning(msg))
06:40:30  Running with dbt=1.10.15
06:40:30  Registered adapter: postgres=1.9.1
06:40:30  Found 3 models, 2 seeds, 447 macros
06:40:30
06:40:30  Concurrency: 4 threads (target='dev')
06:40:30
06:40:30  1 of 2 START seed file public.customers ........................................ [RUN]
06:40:30  2 of 2 START seed file public.orders ........................................... [RUN]
06:40:30  1 of 2 OK loaded seed file public.customers .................................... [INSERT 5 in 0.09s]
06:40:30  2 of 2 OK loaded seed file public.orders ....................................... [INSERT 8 in 0.09s]
06:40:30
06:40:30  Finished running 2 seeds in 0 hours 0 minutes and 0.22 seconds (0.22s).
06:40:30
06:40:30  Completed successfully
06:40:30
06:40:30  Done. PASS=2 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=2
/Users/diegopacheco/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/runpy.py:127: RuntimeWarning: 'dbt.cli.main' found in sys.modules after import of package 'dbt.cli', but prior to execution of 'dbt.cli.main'; this may result in unpredictable behaviour
  warn(RuntimeWarning(msg))
06:40:32  Running with dbt=1.10.15
06:40:32  Registered adapter: postgres=1.9.1
06:40:32  Found 3 models, 2 seeds, 447 macros
06:40:32
06:40:32  Concurrency: 4 threads (target='dev')
06:40:32
06:40:32  1 of 3 START sql view model public.customer_orders ............................. [RUN]
06:40:32  1 of 3 OK created sql view model public.customer_orders ........................ [CREATE VIEW in 0.08s]
06:40:32  2 of 3 START sql view model public.country_sales ............................... [RUN]
06:40:32  3 of 3 START sql view model public.customer_summary ............................ [RUN]
06:40:32  3 of 3 OK created sql view model public.customer_summary ....................... [CREATE VIEW in 0.04s]
06:40:32  2 of 3 OK created sql view model public.country_sales .......................... [CREATE VIEW in 0.05s]
06:40:32
06:40:32  Finished running 3 view models in 0 hours 0 minutes and 0.25 seconds (0.25s).
06:40:32
06:40:32  Completed successfully
06:40:32
06:40:32  Done. PASS=3 WARN=0 ERROR=0 SKIP=0 NO-OP=0 TOTAL=3
/Users/diegopacheco/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/runpy.py:127: RuntimeWarning: 'dbt.cli.main' found in sys.modules after import of package 'dbt.cli', but prior to execution of 'dbt.cli.main'; this may result in unpredictable behaviour
  warn(RuntimeWarning(msg))
06:40:34  Running with dbt=1.10.15
06:40:35  Registered adapter: postgres=1.9.1
06:40:35  Found 3 models, 2 seeds, 447 macros
06:40:35
06:40:35  Concurrency: 4 threads (target='dev')
06:40:35
06:40:35  Building catalog
06:40:35  Catalog written to /Users/diegopacheco/git/diegopacheco/python-playground/dbt-fun/dbt_project/target/catalog.json
Starting dbt docs server on http://localhost:8080
/Users/diegopacheco/Library/Python/3.9/lib/python/site-packages/urllib3/__init__.py:35: NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/lib/python3.9/runpy.py:127: RuntimeWarning: 'dbt.cli.main' found in sys.modules after import of package 'dbt.cli', but prior to execution of 'dbt.cli.main'; this may result in unpredictable behaviour
  warn(RuntimeWarning(msg))
06:40:37  Running with dbt=1.10.15
  ~/git/diegopacheco/python-playground/dbt-fun on   main                               took  9s at  22:40:37
❯ Serving docs at 8080
To access from your browser, navigate to: http://localhost:8080



Press Ctrl+C to exit.
127.0.0.1 - - [16/Nov/2025 22:40:37] "GET / HTTP/1.1" 200 -
127.0.0.1 - - [16/Nov/2025 22:40:37] "GET /manifest.json?cb=1763361637499 HTTP/1.1" 200 -
127.0.0.1 - - [16/Nov/2025 22:40:37] "GET /catalog.json?cb=1763361637499 HTTP/1.1" 200 -
127.0.0.1 - - [16/Nov/2025 22:40:37] code 404, message File not found
127.0.0.1 - - [16/Nov/2025 22:40:37] "GET /%7B%7B%20getIcon(item.type,%20'on')%20%7D%7D HTTP/1.1" 404 -
127.0.0.1 - - [16/Nov/2025 22:40:37] code 404, message File not found
127.0.0.1 - - [16/Nov/2025 22:40:37] "GET /%7B%7B%20getIcon(item.type,%20'off')%20%7D%7D HTTP/1.1" 404 -
```

### Result

```
``` 
