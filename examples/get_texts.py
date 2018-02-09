from contextlib import closing
from data import urls
from requests import get
from tidepool import Pool
from bs4 import BeautifulSoup

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

def add_text(state, text):
    state['texts'].append(text)

if __name__ == '__main__':

    ## new pool
    pool = Pool(
        f=get_text,
        num_procs=4,
        state={'texts': []},
        update=add_text
    )

    ## Run pool and check state
    assert True == pool.run(urls)
    assert len(urls) == len(pool.state['texts'])
    print(pool.state)

    ## shutdown pool and cache
    assert True == pool.shutdown()
    print('Done!')