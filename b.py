from a import *
from threading import Thread
from time import sleep

es_dict = get_all_exceptions()

def do(host_id, node_id):
    restart_secnode(host_id, node_id)
    

for n in es_dict:
    es = es_dict[n]
    if es:
        e = es[0]
        if e.end_at is None and e.etype == 'cert':
             print(n, e)
             # host_id, node_id = e.location
             # restart_secnode(host_id, node_id)
