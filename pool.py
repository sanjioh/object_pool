from pika import exceptions


class ChannelWrapper:
    def __init__(self, pool, channel):
        self._pool = pool
        self._channel = channel
        self.is_valid = True

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if type is not None and isinstance(value, exceptions.AMQPError):
            self.is_valid = False
        self._pool.release(self)

    def __getattr__(self, name):
        return getattr(self._channel, name)


def _default_create(host, port, username, password, vhost):
    credentials = pika.PlainCredentials(username, password)
    conn_params = pika.ConnectionParameters(host, port, vhost, credentials)
    connection = pika.BlockingConnection(conn_params)
    return connection


class Pool:
    def __init__(self, create=None, size=2, wrapper=None):
        self._create = create or _default_create
        self._size = size
        self._wrapper = wrapper or ChannelWrapper
        self._conn = None
        self._channels = []

    def _connect(self):
        self._conn = self._create()

    def _get_channel(self):
        return self._wrapper(self, self._conn.channel())

    def acquire(self):
        if self._conn is None or not self._conn.is_open:
            self._connect()

        while self._channels:
            channel = self._channels.pop(0)
            if channel.is_valid:
                return channel

        return self._get_channel()

    def release(self, channel):
        while not len(self._channels) < self._size:
            self._channels.pop(0)
        self._channels.append(channel)

    def close(self):
        self._conn.close()


def main():
    import json
    import pika
    def create(host, port, username, password, vhost):
        credentials = pika.PlainCredentials(username, password)
        conn_params = pika.ConnectionParameters(host, port, vhost, credentials)
        connection = pika.BlockingConnection(conn_params)
        return connection

    from functools import partial
    real_create = partial(create, 'localhost', 5672, 'agile', 'jd73Hye64bbdb.1', 'test')
    pool = Pool(create=real_create, size=1)
    channel = pool.acquire()

    with channel as ch:
        ch.basic_publish(
            body=json.dumps({'type': 'banana', 'color': 'yellow'}),
            exchange='',
            routing_key='cliqueue',
        )
    s = len(pool._channels)
    with channel as ch:
        ch.basic_publish(
            body=json.dumps({'type': 'banana', 'color': 'yellow'}),
            exchange='',
            routing_key='cliqueue',
        )
    s = len(pool._channels)
    pass


if __name__ == '__main__':
    main()

