import threading
import time


def limit_concurrency():
    semaphore = threading.Semaphore(2)
    active = {"current": 0, "peak": 0}
    lock = threading.Lock()

    def task():
        with semaphore:
            with lock:
                active["current"] += 1
                active["peak"] = max(active["peak"], active["current"])
            time.sleep(0.05)
            with lock:
                active["current"] -= 1

    threads = [threading.Thread(target=task) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return active["peak"]


def bounded_semaphore_guard():
    pool = threading.BoundedSemaphore(1)
    pool.acquire()
    pool.release()
    try:
        pool.release()
        return "over-release allowed"
    except ValueError:
        return "over-release blocked"


def connection_pool():
    slots = threading.Semaphore(3)
    served = []
    lock = threading.Lock()

    def use_connection(client):
        acquired = slots.acquire(timeout=1)
        if not acquired:
            return
        try:
            with lock:
                served.append(client)
            time.sleep(0.02)
        finally:
            slots.release()

    threads = [threading.Thread(target=use_connection, args=(c,)) for c in range(6)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sorted(served)


def main():
    print("limit_concurrency peak (max 2):", limit_concurrency())
    print("bounded_semaphore_guard:", bounded_semaphore_guard())
    print("connection_pool served:", connection_pool())


if __name__ == "__main__":
    main()
