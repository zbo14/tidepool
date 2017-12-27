from multiprocessing import Pipe, Queue
from threading import Thread
import unittest

class Request():
	def __init__(self, key):
		if not isinstance(key, str):
			raise TypeError('key should be str')
		self.key = key

class Get(Request):
	def __init__(self, idx, key):
		super().__init__(key)
		if not isinstance(idx, int):
			raise TypeError('idx should be int')
		self.idx = idx

class Put(Request):
	def __init__(self, key, val):
		super().__init__(key)
		self.val = val

class Cache():

	def __init__(self):
		self.queue = Queue()
		self.pipes = []
		self.state = {}

	def add_pipe(self):
		idx = len(self.pipes)
		(recv, send) = Pipe()
		self.pipes.append(send)
		return (idx, recv)

	def run(self):
		Thread(target=self.loop).start()

	def shutdown(self):
		self.queue.close()
		for pipe in self.pipes:
			pipe.close()
		return True

	def send_to_pipe(self, req, res):
		self.pipes[req.idx].send(res)

	def get(self, idx, key):
		get = Get(idx, key)
		self.queue.put(get, block=True)

	def put(self, key, val):
		put = Put(key, val)
		self.queue.put(put, block=True)

	def loop(self):
		while True:
			try:
				req = self.queue.get(block=True)
				if not isinstance(req, Request):
					print('expected Request')
				elif isinstance(req, Get):
					self.handle_get(req)
				elif isinstance(req, Put):
					self.handle_put(req)
			except EOFError:
				print('Shutting down cache...')
				break

	def handle_get(self, req):
		if req.idx >= len(self.pipes) or req.idx < 0:
			print('unexpected idx: %s' % req.idx)
		else:
			try:
				val = self.state[req.key]
				self.send_to_pipe(req, val)
			except KeyError:
				self.send_to_pipe(req, None)

	def handle_put(self, req):
		self.state[req.key] = req.val

class TestCache(unittest.TestCase):

	def setUp(self):
		self.cache = Cache()
		self.tups = [self.cache.add_pipe() for _ in range(10)]

	def tearDown(self):
		assert True == self.cache.shutdown()

	def gets(self, idx, pipe):
		self.cache.get(idx, 'a')
		self.cache.get(idx, 'b')
		self.cache.get(idx, 'c')
		assert pipe.recv() == 1
		assert pipe.recv() == 2
		assert pipe.recv() == 3

	def test_cache(self):

		from multiprocessing import Process

		self.cache.run()

		self.cache.put('a', 1)
		self.cache.put('b', 2)
		self.cache.put('c', 3)

		procs =	[Process(target=self.gets, args=tup) for tup in self.tups]

		for proc in procs:
			proc.start()

		for proc in procs:
			proc.join()

if __name__ == '__main__':
	unittest.main()