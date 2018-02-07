## tidepool

Process pool for running expensive computation.

For deterministic calculations, results can be cached rather than recomputed.

### Install

Clone the repo and `python3 setup.py install`.

### Usage

Example

```python
from random import randint
from tidepool import Cache
from tidepool import Pool
from time import sleep

if __name__ == '__main__':

    def cube(x):
        ## simulate more expensive computation
        sleep(0.001)
        return x * x * x

    ## update function
    def add_to_total(state, res):
        state['total'] += res

    ## new pool
    pool = Pool(
        f=cube,
        num_procs=4,
        state={'total': 0},
        update=add_to_total,
        cache=Cache()
    )

    ## generate data and calculate sum of cubes
    data = [randint(0, 10) for _ in range(1000)]
    sum_of_cubes = sum([cube(x) for x in data])

    ## run pool and check state
    assert True == pool.run(data)
    assert sum_of_cubes == pool.state['total']

    ## shutdown pool and cache
    assert True == pool.shutdown()
    print('Done!')
```

### Tests

`python3 -m pytest test`
