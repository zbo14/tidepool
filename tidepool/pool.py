from multiprocessing import Pipe, Process, Queue
from threading import Thread
from tidepool.cache import Cache, Get, Put
from tidepool.util import argtypes

NoneType = type(None)

class Pool():

    @argtypes(f=callable, num_procs=int, state=dict, update=callable, cache=(Cache, NoneType), timeout=(int, NoneType))
    def __init__(self, f, num_procs, state, update, cache=None, timeout=None):
        self.cache = cache
        self.count = 0
        self.done = Queue()
        if cache:
            (self.idx, self.pipe) = cache.add_pipe()
            self.cache.run()
        self.procs = []
        self.qin = Queue()
        self.qout = Queue()
        self.state = state
        self.timeout = timeout
        self.update = update
        for _ in range(num_procs):
            proc = Process(target=self.loop, args=(f,))
            self.procs.append(proc)
            proc.start()

    def loop(self, f):
        while True:
            try:
                args = self.qin.get(block=True, timeout=self.timeout)
                res = f(args)
                self.qout.put(res, block=True)
                if self.cache:
                    key = repr(args)
                    self.cache.put(key, res)
            except Exception as e:
                self.done.put(e, block=True)
                break

    def shutdown(self):
        if self.cache:
            assert True == self.cache.shutdown()
        self.done.close()
        self.qin.close()
        self.qout.close()
        for proc in self.procs:
            proc.terminate()
        return True

    def gets(self):
        for _ in range(self.count):
            res = self.qout.get(block=True, timeout=self.timeout)
            self.update(self.state, res)
        self.count = 0
        self.done.put(True, block=True)

    def puts_with_cache(self, list_args):
        for args in list_args:
            key = repr(args)
            self.cache.get(self.idx, key)
            res = self.pipe.recv()
            if res:
                self.qout.put(res, block=True)
            else:
                self.qin.put(args, block=True)

    def puts_without_cache(self, list_args):
        for args in list_args:
            self.qin.put(args, block=True)

    def puts(self, list_args):
        if self.cache:
            self.puts_with_cache(list_args)
        else:
            self.puts_without_cache(list_args)

    @argtypes(list_args=list)
    def run(self, list_args):
        count = len(list_args)
        if count == 0:
            raise ValueError('expected 1 or more args')
        self.count = count
        Thread(target=self.gets).start()
        Thread(target=self.puts, args=(list_args,)).start()
        res = self.done.get(block=True)
        if res:
            return True
        elif isinstance(res, Exception):
            self.shutdown()
            raise res