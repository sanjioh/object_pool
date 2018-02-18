# coding: utf-8
import queue
import threading
from multiprocessing import Queue, RLock


class ObjectWrapper:
    def __init__(self, pool, item):
        self._pool = pool
        self._item = item

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._item is not None:
            self._pool.release(self._item)
            self._item = None

    def __getattr__(self, name):
        return getattr(self._item, name)

    def __del__(self):
        if self._item is not None:
            self._pool.release(self._item)
            self._item = None


class Pool:
    def __init__(self, create, maxsize=None, queue=None, lock=None):
        self._create = create
        self._maxsize = maxsize
        self._queue = queue or Queue()
        self._lock = lock or RLock()
        self._size = 0

    def acquire(self):
        with self._lock:
            block = bool(self._maxsize) and (self._size == self._maxsize)
            try:
                item = self._queue.get(block=block)
            except queue.Empty:
                item = self._create()
                self._size += 1
        return ObjectWrapper(self, item)

    def release(self, item):
        self._queue.put_nowait(item)


def main():
    def create():
        print('created')
        return object()

    pool = Pool(create, maxsize=20)

    def func():
        for _ in range(1000):
            with pool.acquire():
                pass

    threads = [threading.Thread(target=func) for _ in range(100)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    print(pool._queue.qsize())


if __name__ == '__main__':
    main()
