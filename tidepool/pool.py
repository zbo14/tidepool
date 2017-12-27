from cache import Cache, Get, Put
from multiprocessing import Pipe, Process, Queue
from threading import Thread
import unittest
from util import TestError

class Pool():

	def __init__(self, f, num_procs, state, update, cache=None, timeout=None):
		if not callable(f):
			raise TypeError('f should be a function')
		if not isinstance(num_procs, int):
			raise TypeError('num_procs should be int')
		if not isinstance(state, dict):
			raise TypeError('state should be dict')
		if not callable(update):
			raise TypeError('update should be a function')
		if cache is not None and not isinstance(cache, Cache):
			raise TypeError('cache should be Cache')
		if timeout is not None and not isinstance(timeout, int):
			raise TypeError('timeout should be int')
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
		while self.count > 0:
			res = self.qout.get(block=True, timeout=self.timeout)
			self.update(self.state, res)
			self.count -= 1
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

	def run(self, list_args):
		if not isinstance(list_args, list):
			raise TypeError('expected list of args')
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

def add_to_total(state, res):
	state['total'] += res

def cube(x):
	return x * x * x

class TestPool(unittest.TestCase):

	def setUp(self):

		import random

		self.list_args = [random.randint(0, 10) for _ in range(1000)]
		total = sum([arg * arg * arg for arg in self.list_args])
		self.state = {'total': total}

	def test_pool_without_cache(self):
		pool = Pool(f=cube, num_procs=4, state={'total': 0}, update=add_to_total)
		res = pool.run(self.list_args)
		self.assertEqual(res, True)
		self.assertEqual(pool.state, self.state)
		assert True == pool.shutdown()

	def test_pool_with_cache(self):
		pool = Pool(f=cube, num_procs=4, state={'total': 0}, update=add_to_total, cache=Cache())
		res = pool.run(self.list_args)
		self.assertEqual(res, True)
		self.assertEqual(pool.state, self.state)
		assert True == pool.shutdown()

def test_bad_pool_args_(**kwargs):
	try:
		pool = Pool(**kwargs)
		raise TestError('Expected TypeError')
	except TypeError:
		return

class TestBadArgs(unittest.TestCase):

	def test_bad_pool_args(self):
		test_bad_pool_args_(f=1, num_procs=4, state={'total': 0}, update=add_to_total, cache=Cache(), timeout=30)
		test_bad_pool_args_(f=cube, num_procs='four', state={'total': 0}, update=add_to_total, cache=Cache(), timeout=30)
		test_bad_pool_args_(f=cube, num_procs=4, state=[0], update=add_to_total, cache=Cache(), timeout=30)
		test_bad_pool_args_(f=cube, num_procs=4, state={'total': 0}, update={}, cache=0, timeout=30)
		test_bad_pool_args_(f=cube, num_procs=4, state={'total': 0}, update=add_to_total, cache=0, timeout=30)
		test_bad_pool_args_(f=cube, num_procs=4, state={'total': 0}, update=add_to_total, cache=None, timeout=300.1)

	def test_bad_run_args(self):
		pool = Pool(f=cube, num_procs=4, state={'total': 0}, update=add_to_total)
		try:
			pool.run({})
			raise TestError('Expected TypeError')
		except TypeError:
			try:
				pool.run([])
				raise TestError('Expected ValueError')
			except ValueError:
				return

if __name__ == '__main__':
	unittest.main()