import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def basic_thread():
    result = []

    def worker(n):
        result.append(n * n)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sorted(result)


def thread_with_lock():
    lock = threading.Lock()
    counter = {"value": 0}

    def increment():
        for _ in range(10000):
            with lock:
                counter["value"] += 1

    threads = [threading.Thread(target=increment) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return counter["value"]


def thread_pool():
    def slow_square(n):
        time.sleep(0.05)
        return n * n

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(slow_square, i) for i in range(8)]
        return sorted(f.result() for f in as_completed(futures))


def result_via_queue():
    output = queue.Queue()

    def producer(n):
        output.put(n * 10)

    threads = [threading.Thread(target=producer, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return sorted(output.get() for _ in range(5))


def daemon_thread():
    ticks = {"count": 0}

    def background():
        while True:
            ticks["count"] += 1
            time.sleep(0.01)

    t = threading.Thread(target=background, daemon=True)
    t.start()
    time.sleep(0.05)
    return ticks["count"] > 0


def main():
    print("basic_thread:", basic_thread())
    print("thread_with_lock:", thread_with_lock())
    print("thread_pool:", thread_pool())
    print("result_via_queue:", result_via_queue())
    print("daemon_thread ran:", daemon_thread())


if __name__ == "__main__":
    main()
