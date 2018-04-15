import queue
import threading
import time
import weakref
from multiprocessing import RLock
from queue import Queue


class ObjectWrapper:
    def __init__(self, pool, item):
        self._pool = pool
        self._item = item

    def __enter__(self):
        print(f'enter: {id(self._item)}')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print(f'exit: {id(self._item)}')
        if self._item is not None:
            self._pool.release(self._item)
            self._item = None

    def __getattr__(self, name):
        return getattr(self._item, name)


class Pool:
    def __init__(self, create, maxsize=None, queue=None, lock=None):
        self._create = create
        self._maxsize = maxsize
        self._queue = queue or Queue()
        self._lock = lock or RLock()
        self._refs = weakref.WeakSet()
        # self._refs = set()

    def acquire(self):
        with self._lock:
            block = bool(self._maxsize) and (len(self._refs) == self._maxsize)
            try:
                item = self._queue.get(block=block)
            except queue.Empty:
                item = self._create()
                self._refs.add(item)
                # print(len(self._refs))
        return ObjectWrapper(self, item)

    def release(self, item):
        self._queue.put_nowait(item)
        print(f'released: {id(item)}')


class C:
    def __init__(self):
        print(f'created: {id(self)}')

    def __del__(self):
        print(f'deleted: {id(self)}')


def main():

    pool = Pool(C, maxsize=1)

    def func():
        for _ in range(1):
            with pool.acquire():
                pass

    threads = [threading.Thread(target=func) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # print(pool._queue.get())
    # print(pool._queue.get())
    print(pool._queue.qsize())


if __name__ == '__main__':
    main()
