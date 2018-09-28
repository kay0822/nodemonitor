from monitor import *
from threading import Thread
from time import sleep

es_dict = get_all_exceptions()
ns_dict = get_all_nodes()

el = ((29, 26))


for fqdn, ex in es_dict.items():
    try:
        location = parse_fqdn(fqdn)
    except:
        continue
    print(location)
    if location in el:
        print(ex)


# for n in es_dict:
#     es = es_dict[n]
#     
#     if es:
#         e = es[0]
#         if e.end_at is None and e.etype == 'chal':
#              host_id, node_id = e.location
#              home = e.home
#              if host_id in [17, 18]:
#                  continue
#              print(ns_dict[n], e)
#              #print(n, e)
#              # host_id, node_id = e.location
#              # restart_secnode(host_id, node_id)
