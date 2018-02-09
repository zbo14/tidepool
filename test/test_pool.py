import pytest
import unittest
from bs4 import BeautifulSoup
from contextlib import closing
from test.data import nums, urls
from random import randint
from requests import get
from tidepool import Cache, Pool
from time import sleep

def add_to_total(state, num):
    state['total'] += num

def add_text(state, text):
    state['texts'].append(text)

def cube(x):
    return x * x * x

## adapted from https://realpython.com/blog/python/python-web-scraping-practical-introduction/

def get_text(url):
    try:
        with closing(get(url, stream=True)) as resp:
            content_type = resp.headers['Content-Type'].lower()
            if resp.status_code != 200:
                raise Exception('expected 200 status_code, got ' + resp.status_code)
            elif 'html' not in content_type:
                raise Exception('expected html content_type, got ' + content_type)
            else:
                html = BeautifulSoup(resp.content, 'html.parser')
                return html.get_text()
    except Exception as e:
        print('Error in request to {0} : {1}'.format(url, str(e)))
        return None

def sum_of_cubes(nums):
    return sum([cube(x) for x in nums])

def get_texts(urls):
    return [get_text(url) for url in urls]

def expected_type_error():
    raise Exception('expected TypeError')

def new_pool():
    return Pool(
        f=get_text, 
        num_procs=4, 
        state={'texts': []}, 
        update=add_text
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
        self.pool = new_pool()
        self.pool_with_cache = new_pool_with_cache()

    def tearDown(self):
        assert True == self.pool.shutdown()
        assert True == self.pool_with_cache.shutdown()

    def test_pool_without_cache(self):
        assert True == self.pool.run(urls)
        assert len(self.pool.state['texts']) == len(urls)

    def test_pool_with_cache(self):
        assert True == self.pool_with_cache.run(nums)
        assert self.pool_with_cache.state['total'] == sum_of_cubes(nums)

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

pool = new_pool()
pool_with_cache = new_pool_with_cache()
total = sum_of_cubes(nums)

def run_pool_with_cache(pool, nums, total):
    assert True == pool.run(nums)
    assert total == pool.state['total']
    pool.state['total'] = 0

def test_pool_with_cache(benchmark):
    benchmark(run_pool_with_cache, pool_with_cache, nums, total)

def test_sum_of_cubes(benchmark):
    benchmark(sum_of_cubes, nums)

def run_pool(pool, urls):
    assert True == pool.run(urls)
    assert len(urls) == len(pool.state['texts'])
    pool.state['texts'] = []

def test_pool(benchmark):
    benchmark(run_pool, pool, urls)

def test_get_texts(benchmark):
    benchmark(get_texts, urls)

if __name__ == '__main__':
    unittest.main()