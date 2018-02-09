from data import nums
from random import randint
from tidepool import Cache, Pool
from time import sleep

def cube(x):
    return x * x * x

## update function
def add_to_total(state, res):
    state['total'] += res

if __name__ == '__main__':

    ## new pool
    pool = Pool(
        f=cube, 
        num_procs=4, 
        state={'total': 0}, 
        update=add_to_total, 
        cache=Cache()
    )

    ## generate data and calculate sum of cubes
    sum_of_cubes = sum([cube(x) for x in nums])

    ## run pool and check state
    assert True == pool.run(nums)
    assert sum_of_cubes == pool.state['total']

    ## shutdown pool and cache 
    assert True == pool.shutdown()
    print('Done!')