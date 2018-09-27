from a import *
from threading import Thread
from time import sleep

# ns_dict = get_all_nodes()
# 
# for n in es_dict:
#     es = es_dict[n]
#     if es:
#         e = es[0]
#         if e.end_at is None and e.etype == 'chal':
#              host_id, node_id = e.location
#              home = e.home
#              if host_id in [17, 18]:
#                  continue
#              #print(ns_dict[n], e)
#              print(n, e)
#              # host_id, node_id = e.location
#              # restart_secnode(host_id, node_id)
# 

my_dict = {
26: [35,8,11,32,33,10,30,24,27,20],
}

for hid in my_dict:
    node_id_list = my_dict[hid]
    for nid in node_id_list:
        ns_dict = get_all_nodes()
        for fqdn, node in ns_dict.items():
            host_id, node_id = node.location
            if host_id == hid and node_id == nid:
                print(node)
                curserver = node.curserver
                do_challenge(host_id, node_id, curserver)
                sleep(2000)
