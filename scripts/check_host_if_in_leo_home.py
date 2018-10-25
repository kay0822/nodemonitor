#!/usr/bin/env python
from monitor import *

default_only_hosts = [16, 19, 20] + list(range(21, 31)) + list(range(31, 41))
default_hosts_in_leo_home = [20]

if __name__ == '__main__':
    hosts = [ host_id for host_id in default_only_hosts if host_id not in default_hosts_in_leo_home ]
    for host_id in hosts:
        try:
            cmd = 'ssh z%d \'for i in {1..80};do snget $i rpchost 2> /dev/null; done\'' % host_id
            output = subprocess.check_output(cmd, shell=True)
            print(output)
        except subprocess.CalledProcessError:
            logger.warning('ssh failed, host_id: {}'.format(host_id))

