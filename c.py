from a import *
from threading import Thread
from time import sleep

es_dict = get_all_exceptions()

for n in es_dict:
    
    es = es_dict[n]
    if es:
        e = es[0]
        if e.end_at is None and e.etype == 'peers':
             print(n, e)
             # host_id, node_id = e.location
             # home = e.home
             # snset(host_id, node_id, 'home', home)
             # restart_secnode(host_id, node_id)
