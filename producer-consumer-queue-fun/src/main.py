import time
from queue import Empty, Queue
from threading import Thread


def producer(queue,how_much):
    for i in range(1, how_much):
        print(f'[>>> Producer] put item {i} into the queue')
        time.sleep(1)
        queue.put(i)

def consumer(queue):
    while True:
        try:
            item = queue.get()
            print("[<<< Consumer] Got item: " + str(item))
        except Empty:
            continue
        else:
            print(f'[<<< Consumer] Processing item {item}')
            time.sleep(2)
            queue.task_done()

def main():
    queue = Queue()

    threads = [
        Thread(
            target=producer,
            args=(queue,10)
        ),
        Thread(
            target=consumer,
            args=(queue,),
            daemon=True
        )
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    #queue.join()

if __name__ == '__main__':
    main()