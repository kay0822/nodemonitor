from monitor import *
from threading import Thread
from time import sleep

ns_dict = get_all_nodes()

a = ((32,1),(32,2),(32,3))
for fqdn, node in ns_dict.items():
    host_id, node_id = node.location
    home = node.home
    if home == 'ts2.na':
        print(host_id, node_id)
        snset(host_id, node_id, 'home', 'ts3.na')
        restart_secnode(host_id, node_id)
    #if (host_id, node_id) in a:
    #    print(node)
