from a import *
from threading import Thread
from time import sleep

ds_dict = get_all_downtimes()


for n in ds_dict:
    ds = ds_dict[n]
    if ds:
        d = ds[0]
        if d.end_at is None and d.dtype == 'sys':
             host_id, node_id = d.location
             home = d.home
             curserver = d.curserver

             print(n, d)
             if host_id in [17,18]:
                 continue
             
             down_server = 'ts4.eu'
             if curserver == down_server or home == down_server:
                 snset(host_id, node_id, 'home', 'ts1.eu')
             restart_secnode(host_id, node_id)
