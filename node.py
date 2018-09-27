from monitor import *
from threading import Thread
from time import sleep

ns_dict = get_all_nodes()

a = ((32,1),(32,2),(32,3))
for fqdn, node in ns_dict.items():
    host_id, node_id = node.location
    if (host_id, node_id) in a:
        print(node)


# my_dict = {
# 26: [35,8,11,32,33,10,30,24,27,20],
# }
# 
# for hid in my_dict:
#     node_id_list = my_dict[hid]
#     for nid in node_id_list:
#         ns_dict = get_all_nodes()
#         for fqdn, node in ns_dict.items():
#             host_id, node_id = node.location
#             if host_id == hid and node_id == nid:
#                 print(node)
#                 curserver = node.curserver
#                 do_challenge(host_id, node_id, curserver)
#                 sleep(2000)
