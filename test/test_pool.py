import pytest
import unittest
from random import randint
from tidepool import Cache
from tidepool import Pool
from time import sleep

def add_to_total(state, res):
    state['total'] += res

def cube(x):
    sleep(0.001)
    return x * x * x

def sum_of_cubes(data):
    return sum([cube(x) for x in data])

def expected_type_error():
    raise Exception('expected TypeError')

def new_pool():
    return Pool(
        f=cube, 
        num_procs=4, 
        state={'total': 0}, 
        update=add_to_total
    )

def new_pool_with_cache():
    return Pool(
        f=cube, 
        num_procs=4, 
        state={'total': 0}, 
        update=add_to_total,
        cache=Cache()
    )

class TestPool(unittest.TestCase):

    def setUp(self):
        self.data = [randint(0, 10) for _ in range(1000)]
        total = sum_of_cubes(self.data)
        self.state = {'total': total}
        self.pool = new_pool()
        self.pool_cache = new_pool_with_cache()

    def tearDown(self):
        assert True == self.pool.shutdown()
        assert True == self.pool_cache.shutdown()

    def test_pool_without_cache(self):
        res = self.pool.run(self.data)
        self.assertEqual(res, True)
        self.assertEqual(self.pool.state, self.state)

    def test_pool_with_cache(self):
        res = self.pool_cache.run(self.data)
        self.assertEqual(res, True)
        self.assertEqual(self.pool_cache.state, self.state)

def test_bad_pool_args_(**kwargs):
    try:
        pool = Pool(**kwargs)
        expected_type_error()
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
            expected_type_error()
        except TypeError:
            try:
                pool.run([])
                expected_type_error()
            except ValueError:
                return

## Benchmark

data = [randint(0, 10) for _ in range(1000)]
pool = new_pool_with_cache()
total = sum_of_cubes(data)

def run_pool(pool, data, total):
    assert True == pool.run(data)
    assert total == pool.state['total']
    pool.state['total'] = 0

def test_pool(benchmark):
    benchmark(run_pool, pool, data, total)

def test_sum_of_cubes(benchmark):
    benchmark(sum_of_cubes, data)

if __name__ == '__main__':
    unittest.main()