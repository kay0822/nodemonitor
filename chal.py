from monitor import *
from threading import Thread
from time import sleep

es_dict = get_all_exceptions()
ns_dict = get_all_nodes()

for n in es_dict:
    es = es_dict[n]
    if es:
        e = es[0]
        if e.end_at is None and e.etype == 'chal':
             host_id, node_id = e.location
             home = e.home
             if host_id in [17, 18] or host_id > 40:
                 continue
                 
             if n in ns_dict:
                 if 30 * 60 * 1000 < e.duration < 110 * 60 * 1000:
                     print(ns_dict[n], e)
                     #do_challenge(host_id, node_id)
               


             #  # snset(host_id, node_id, 'home', 'ts2.eu')
             #  snset(host_id, node_id, 'rpchost', 'bibenwei.com')
             #  if host_id == 28:
             #      snset(host_id, node_id, 'rpcport', 22203)
             #  elif host_id == 29:
             #      snset(host_id, node_id, 'rpcport', 22204)
             #  elif host_id == 19 and node_id < 30:
             #      snset(host_id, node_id, 'rpcport', 22201)
             #  elif host_id == 19:
             #      snset(host_id, node_id, 'rpcport', 22202)
             #  restart_secnode(host_id, node_id)
