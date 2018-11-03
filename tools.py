from bitcoin.rpc import RawProxy
from time import sleep

rpc = RawProxy('http://{}:{}@localhost:8231'.format(username, password))

def call(func_name, *args, **kwargs):
    while True:
        try:
            f = getattr(rpc, func_name)
            return f(*args, **kwargs)
        except:
            print('pipe broken while calling {}, args: {}, kwargs: {}'.format(func_name, args, kwargs))
            rpc.close()
            sleep(0.5)

try:
    from insight_pyclient.insight_api import InsightApi
    api = InsightApi('http://localhost:3001/api/')
    api.timeout = 10
except:
    print('no insight_pyclient, can ignore')
