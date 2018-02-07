import unittest
from tidepool import Cache

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

        procs = [Process(target=self.gets, args=tup) for tup in self.tups]

        for proc in procs:
            proc.start()

        for proc in procs:
            proc.join()

if __name__ == '__main__':
    unittest.main()