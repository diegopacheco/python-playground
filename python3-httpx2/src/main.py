import asyncio
import sys

import client


def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
    with client.build(base_url) as http:
        print("health           ", client.health(http))
        print("users            ", [u["name"] for u in client.users(http)])
        print("echo             ", client.echo(http, {"lang": "python", "version": "3.14.6"}))
        print("query search     ", [u["name"] for u in client.search(http, {"lang": "python"})])
        print("stream           ", client.stream_lines(http, 4))
        print("sse              ", client.events(http, 3))
        print("basic auth       ", client.secure(http, "admin", "secret"))
        print("status error     ", client.status_error(http, 503))
        print("read timeout     ", client.read_timeout(http, 1.0))
    print("async concurrent ", asyncio.run(client.concurrent_health(base_url, 5)))


if __name__ == "__main__":
    main()
