#!/usr/bin/env python
import logging
import os
import requests
import re
from time import time, sleep
import dateutil.parser
from datetime import datetime
from collections import defaultdict
import subprocess
logger = logging.getLogger(__name__)
from personal import *

"""
https://securenodes.eu.zensystem.io/api/nodes/my/list?key=<key>
https://securenodes.eu.zensystem.io/api/nodes/my/challenges?key=<key>&page=1&rows=10000
https://securenodes.eu.zensystem.io/api/nodes/89156/detail?key=<key>

"""
ROWS = 2000

for email, key in apikeys.items():
    email = email.strip()
    key = key.strip()

base_url = 'https://securenodes.eu.zensystem.io'
default_exclude_hosts = [17, 18]
# default_only_hosts = [
#     19, 
#     20, 
#     21,
#     22,
#     23, 
#     31,
#     38,
# ]
default_only_hosts = list(range(21, 34 + 1)) + list(range(36, 48 + 1))
default_hosts_in_leo_home = [20]
default_ignore_etype = ('stkbal', 'chalmax', 'stk42')
default_ignore_dtype = ()

def parse_fqdn(fqdn):
    hostname = fqdn.split('.')[0]
    host_id, node_id = re.compile(r'[a-z]+(\d+)[a-z]+(\d+)').match(hostname).groups()
    return int(host_id), int(node_id)

def parse_fqdn2(fqdn):
    hostname = fqdn.split('.')[0]
    host_name, node_name = re.compile(r'([a-z]+\d+)([a-z]+\d+)').match(hostname).groups()
    return int(host_name), int(node_name)

def parse_date(d):
    return int(dateutil.parser.parse(d).timestamp() * 1000) if d else d

def parse_home(home):
    server_id, region = re.compile(r'ts(\d+)\.(\w+)').match(home).groups()    
    return int(server_id), region

def parse_url(url):
    protocol, server_id, region, chal_id = re.compile(r'(http://|https://)?securenodes(\d+)\.(\w+)\.zensystem.io/chal/(\w+)/single.*').match(url).groups()
    return int(server_id), region, chal_id

def gen_url(server_id, region, chal_id):
    return 'https://securenodes{}.{}.zensystem.io/chal/{}/single'.format(server_id, region, chal_id)

def gen_real_url(url, server_id, region):
    _, _, chal_id = parse_url(url)
    return gen_url(server_id, region, chal_id)

class Node:
    def __init__(self, id, fqdn, home, curserver, email, create_at, update_at, status, category):
        self.id = id
        self.fqdn = fqdn
        self.home = home
        self.curserver = curserver
        self.email = email
        self.create_at = create_at
        self.update_at = update_at
        self.status = status
        self.category = category
        self.chals = []
        self.exceptions = []
        self.downtimes = []

        if self.status == 'up':
            self.is_up = True
        else:
            self.is_up = False

        try:
            self.location = parse_fqdn(self.fqdn)
        except:
            self.location = None

        try:
            self.host_name, self.node_name = parse_fqdn2(self.fqdn)
        except:
            self.host_name, self.node_name = None, None

    def is_valid(self):
        if self.location is None:
            return False
        if self.status == 'dead':
            return False
        if self.create_at is None or self.update_at is None:
            return False
        if self.category and self.category == 'disabled':
            return False
        return True

    def is_no_exception_or_downtime(self, ignore=True):
        """
        @param ignore: 是否忽略那些可以忽略的type
        """
        if self.exceptions:
            if ignore:
                exs = [ex for ex in self.exceptions if not ex.can_ignore()]
                if exs:
                    return False
            else:
                return False
        if self.downtimes:
            if ignore:
                dts = [dt for dt in self.downtimes if not dt.can_ignore()]
                if dts:
                    return False
            else:
                return False
        return True

    def is_pass(self, ignore=True):
        """
        @param ignore: 是否忽略那些可以忽略的type
        """
        if self.exceptions:
            if ignore:
                exs = [ex for ex in self.exceptions if not ex.can_ignore()]
                if exs:
                    return False
            else:
                return False
        if self.downtimes:
            if ignore:
                dts = [dt for dt in self.downtimes if not dt.can_ignore()]
                if dts:
                    return False
            else:
                return False
        if not self.chals:
            # 没有挑战视为pass
            return True
        else:
            return self.chals[0].is_pass()

    def dump(self):
        logger.debug('node: {}'.format(self))
        if self.chals:
            logger.debug('    chal: {}'.format(self.chals[0]))
        if self.exceptions:
            logger.debug('    ex: {}'.format(self.exceptions[0]))
        if self.downtimes:
            logger.debug('    dt: {}'.format(self.downtimes[0]))

    # 7days = 7 * 3600 * 24 * 1000 = 604800000
    def is_expired(self, now=None, duration=604800000):
        if now is None:
            now = int(time() * 1000)
        
        if self.update_at:
            if now - self.update_at > duration:
                expired = True 
            else:
                expired = False
        else:
            expired = True 
        return expired

    def __repr__(self):
        return 'Node(id={}, fqdn={}, home={}, curserver={}, email={}, create_at={}, update_at={}, status={})'.format(
            self.id,
            self.fqdn,
            self.home,
            self.curserver,
            self.email,
            #self.create_at,
            #self.update_at,
            datetime.fromtimestamp(self.create_at / 1000),
            datetime.fromtimestamp(self.update_at / 1000),
            self.status,
        )

class Chal:
    def __init__(self, id, nid, fqdn, home, start_at, receive_at, reply, run, result, reason):
        self.id = id
        self.nid = nid
        self.fqdn = fqdn
        self.home = home
        self.start_at = start_at
        self.receive_at = receive_at
        self.reply = reply
        self.run = run
        self.result = result
        self.reason = reason
        try:
            self.location = parse_fqdn(self.fqdn)
        except:
            self.location = None

        try:
            self.host_name, self.node_name = parse_fqdn2(self.fqdn)
        except:
            self.host_name, self.node_name = None, None

    def is_overlap(self):
        if self.result == 'overlap':
            return True
        else:
            return False

    def is_pass(self):
        if self.result == 'pass':
            return True
        else:
            return False

    @property
    def is_open(self):
        return not self.is_pass

    def is_valid(self):
        if self.location is None:
            return False
        if self.start_at is None:
            return False
        return True

    # 10days = 10 * 3600 * 24 * 1000 = 864000000
    def is_expired(self, now=None, duration=864000000):
        if now is None:
            now = int(time() * 1000)
        
        if now - self.start_at > duration:
            expired = True 
        else:
            expired = False
        return expired

    def __repr__(self):
        return 'Chal(id={}, nid={}, fqdn={}, home={}, start_at={}, receive_at={}, reply={}, run={}, result={}, reason={})'.format(
            self.id,
            self.nid,
            self.fqdn,
            self.home,
            datetime.fromtimestamp(self.start_at / 1000),
            datetime.fromtimestamp(self.receive_at / 1000) if self.receive_at else self.receive_at,
            self.reply,
            self.run,
            self.result,
            self.reason,
        )

class Downtime:
    def __init__(self, id, nid, fqdn, home, curserver, start_at, check_at, end_at, duration, dtype):
        self.id = id
        self.nid = nid
        self.fqdn = fqdn
        self.home = home
        self.curserver = curserver
        self.start_at = start_at
        self.check_at = check_at
        self.end_at = end_at
        self.duration = duration
        self.dtype = dtype
        try:
            self.location = parse_fqdn(self.fqdn)
        except:
            self.location = None

        try:
            self.host_name, self.node_name = parse_fqdn2(self.fqdn)
        except:
            self.host_name, self.node_name = None, None

    def is_valid(self):
        if self.location is None:
            return False
        if self.start_at is None:
            return False
        return True

    @property
    def is_open(self):
        return self.end_at is None

    def can_ignore(self):
        return self.dtype in default_ignore_dtype

    # 10days = 10 * 3600 * 24 * 1000 = 864000000
    def is_expired(self, now=None, duration=864000000):
        if self.is_open:
            return False
        if now is None:
            now = int(time() * 1000)
        if now - self.start_at > duration:
            expired = True
        else:
            expired = False
        return expired

    def __repr__(self):
        return 'Downtime(id={}, nid={}, fqdn={}, home={}, curserver={}, start_at={}, check_at={}, end_at={}, duration={}, dtype={})'.format(
            self.id,
            self.nid,
            self.fqdn,
            self.home,
            self.curserver,
            datetime.fromtimestamp(self.start_at / 1000),
            datetime.fromtimestamp(self.check_at / 1000) if self.check_at else self.check_at,
            datetime.fromtimestamp(self.end_at / 1000) if self.end_at else self.end_at,
            self.duration,
            self.dtype,
        )

class Ex:
    def __init__(self, id, nid, fqdn, home, start_at, check_at, end_at, duration, etype, detail=None):
        self.id = id
        self.nid = nid 
        self.fqdn = fqdn
        self.home = home
        self.start_at = start_at
        self.check_at = check_at
        self.end_at = end_at
        self.duration = duration
        self.etype = etype
        self.detail = detail

        try:
            self.location = parse_fqdn(self.fqdn)
        except:
            self.location = None

        try:
            self.host_name, self.node_name = parse_fqdn2(self.fqdn)
        except:
            self.host_name, self.node_name = None, None

    def is_valid(self):
        if self.location is None:
            return False
        if self.start_at is None:
            return False
        return True

    @property
    def is_open(self):
        return self.end_at is None

    def can_ignore(self):
        return self.etype in default_ignore_etype

    # 10days = 10 * 3600 * 24 * 1000 = 864000000
    def is_expired(self, now=None, duration=864000000):
        if self.is_open:
            return False

        if now is None:
            now = int(time() * 1000)
        if now - self.start_at > duration:
            expired = True
        else:
            expired = False
        return expired

    def __repr__(self):
        return 'Ex(id={}, nid={}, fqdn={}, home={}, start_at={}, check_at={}, end_at={}, duration={}, etype={}, detail={})'.format(
            self.id,
            self.nid,
            self.fqdn,
            self.home,
            datetime.fromtimestamp(self.start_at / 1000),
            datetime.fromtimestamp(self.check_at / 1000) if self.check_at else self.check_at,
            datetime.fromtimestamp(self.end_at / 1000) if self.end_at else self.end_at,
            self.duration,
            self.etype,
            self.detail,
        )   


def get_nodes(key):
    params = {'key': key}
    url = '{}/api/nodes/my/list'.format(base_url)
    response = requests.get(
        url,
        params=params,
    )
    resp = response.json()
    _nodes = resp['nodes']
    nodes = []
    for n in _nodes:
        create_at = parse_date(n['createdAt'])
        update_at = parse_date(n['updatedAt'])

        node = Node(
            n['id'],
            n['fqdn'],
            n['home'],
            n['curserver'],
            n['email'],
            create_at,
            update_at,
            n['status'],
            n.get('category', None),
        )
        nodes.append(node)
    return nodes
            

def get_chals(key):
    params = {'key': key, 'page': 1, 'rows': ROWS}
    url = '{}/api/nodes/my/challenges'.format(base_url)
    response = requests.get(
        url,
        params=params,
    )
    resp = response.json()
    rows = resp['rows']
    chals = []
    for r in rows:
        start_at = parse_date(r['start'])
        receive_at = parse_date(r['received'])
        chal = Chal(
            r['id'],
            r['nid'],
            r['fqdn'],
            r['home'],
            start_at,
            receive_at,
            r['reply'],
            r['run'],
            r['result'],
            r['reason'],
        )
        chals.append(chal)
    return chals

def get_downtimes(key, opened_only=True):
    params = {'key': key, 'page': 1, 'rows': ROWS}
    if opened_only:
        params['status'] = 'o'

    url = '{}/api/nodes/my/downtimes'.format(base_url)
    response = requests.get(
        url,
        params=params,
    )
    resp = response.json()
    rows = resp['rows']
    downtimes = []
    for r in rows:
        start_at = parse_date(r['start'])
        check_at = parse_date(r['check'])
        end_at = parse_date(r['end'])
        downtime = Downtime(
            r['id'],
            r['nid'],
            r['fqdn'],
            r['home'],
            r['curserver'],
            start_at,
            check_at,
            end_at,
            r['duration'],
            r['dtype'],
        )
        downtimes.append(downtime)
    return downtimes

def get_exceptions(key, opened_only=True):
    params = {'key': key, 'page': 1, 'rows': ROWS}
    if opened_only:
        params['status'] = 'o'

    url = '{}/api/nodes/my/exceptions'.format(base_url)
    response = requests.get(
        url,
        params=params,
    )
    resp = response.json()
    rows = resp['rows']
    exceptions = []
    for r in rows:
        start_at = parse_date(r['start'])
        check_at = parse_date(r['check'])
        end_at = parse_date(r['end'])
        if 'etype' not in r:
            print(r)
        ex = Ex(
            r['id'],
            r['nid'],
            r['fqdn'],
            r['home'],
            start_at,
            check_at,
            end_at,
            r['duration'],
            r['etype'],
        )
        exceptions.append(ex)
    return exceptions


def get_valid_chals(email, key):
    valid_chals = []
    now = int(time() * 1000)
    chals = get_chals(key)
    for chal in chals:
        if chal.is_valid() and not chal.is_expired(now=now):
            # if chal.result == 'overlap':
            #     # 第一个挑战有可能是overlap的，需要把overlap的去掉
            #     #logger.debug('overlap challenge marked as invalid')
            #     pass
            # else:
            #     valid_chals.append(chal)
            valid_chals.append(chal)
        else:
            pass  # invalid
    return valid_chals


def get_all_chals():
    """
    dict
        key: fqdn, value: chal_list
    """
    chals_dict = defaultdict(lambda: [])
    for email, key in apikeys.items():
        valid_chals = get_valid_chals(email, key)
        for chal in valid_chals:
            chals_dict[chal.fqdn].append(chal)
    return chals_dict

def get_valid_nodes(email, key):
    valid_nodes = []
    now = int(time() * 1000)
    nodes = get_nodes(key)
    for node in nodes:
        if node.is_valid() and not node.is_expired(now=now):
            if node.email == email:
                valid_nodes.append(node)
            else:
                logger.warning('email != node.email, invalid, email: {}, node: {}'.format(email, node))
        else:
            pass  # invalid not expired
    return valid_nodes

def get_all_nodes():
    """
    dict
        key: fqdn, value: node
    """
    nodes_dict = {}
    for email, key in apikeys.items():
        valid_nodes = get_valid_nodes(email, key)
        for node in valid_nodes:
            nodes_dict[node.fqdn] = node
    return nodes_dict

def get_valid_downtimes(email, key, opened_only=True):
    valid_downtimes = []
    now = int(time() * 1000)
    downtimes = get_downtimes(key, opened_only=opened_only)
    for downtime in downtimes:
        if downtime.is_valid() and not downtime.is_expired(now=now):
            valid_downtimes.append(downtime)
        else:
            pass  # invalid
    return valid_downtimes

def get_all_downtimes():
    """
    dict
        key: fqdn, value: chal_list
    """
    downtimes_dict = defaultdict(lambda: [])
    for email, key in apikeys.items():
        valid_downtimes = get_valid_downtimes(email, key)
        for downtime in valid_downtimes:
            downtimes_dict[downtime.fqdn].append(downtime)
    return downtimes_dict

def get_valid_exceptions(email, key, opened_only=True):
    valid_exceptions = []
    now = int(time() * 1000)
    exceptions = get_exceptions(key, opened_only=opened_only)
    for ex in exceptions:
        if ex.is_valid() and not ex.is_expired(now=now):
            valid_exceptions.append(ex)
        else:
            pass  # invalid
    return valid_exceptions
    
def get_all_exceptions():
    """
    dict
        key: fqdn, value: chal_list
    """ 
    exceptions_dict = defaultdict(lambda: [])
    for email, key in apikeys.items():
        valid_exceptions = get_valid_exceptions(email, key)
        for ex in valid_exceptions:
            exceptions_dict[ex.fqdn].append(ex)
    return exceptions_dict

#
# 归类函数
#
def get_all_nodes_by_host(nodes_dict=None, exclude=None, only=None):
    """
    dict
        key: host_id, value: node_list
    """
    if nodes_dict is None:
        nodes_dict = get_all_nodes()
    if exclude is None:
        exclude = default_exclude_hosts
    if only is None:
        only = default_only_hosts
    nodes_by_host_dict = defaultdict(lambda: [])
    for fqdn, node in nodes_dict.items():
        host_id = node.location[0]
        if only:
            if host_id in only:
                nodes_by_host_dict[host_id].append(node)
        else:
            if host_id in exclude:
                continue
            nodes_by_host_dict[host_id].append(node)
    return nodes_by_host_dict

def get_all_nodes_chals_by_host():
    nodes_dict = get_all_nodes_by_host()
    chals_dict = get_all_chals()
    for host_id, nodes in nodes_dict.items():
        for node in nodes:
            chals = chals_dict[node.fqdn]
            node.chals = sorted(chals, key=lambda chal:chal.start_at, reverse=True)
    return nodes_dict

from threading import Thread
from queue import Queue

def get_valid_nodes_thread(queue, email, key):
    valid_nodes = None
    try:
        valid_nodes = get_valid_nodes(email, key)
    except:
        pass
    queue.put(valid_nodes)
    
def get_valid_chals_thread(queue, email, key):
    valid_chals = None
    try:
        valid_chals = get_valid_chals(email, key)
    except:
        pass
    queue.put(valid_chals)
    
def get_valid_excpetions_thread(queue, email, key, opened_only=True):
    valid_excpetions = None
    try:
        valid_excpetions = get_valid_exceptions(email, key, opened_only=opened_only)
    except:
        pass
    queue.put(valid_excpetions)
    
def get_valid_downtimes_thread(queue, email, key, opened_only=True):
    valid_downtimes = None
    try:
        valid_downtimes = get_valid_downtimes(email, key, opened_only=opened_only)
    except:
        pass
    queue.put(valid_downtimes)

def get_everything(exclude=None, only=None, opened_only=True):
    node_queues = []
    chal_queues = []
    exception_queues = []
    downtime_queues = []
    for email, key in apikeys.items():
        node_queue = Queue()
        Thread(target=get_valid_nodes_thread, args=(node_queue, email, key), daemon=True).start()
        node_queues.append(node_queue)

        chal_queue = Queue()
        Thread(target=get_valid_chals_thread, args=(chal_queue, email, key), daemon=True).start()
        chal_queues.append(chal_queue)

        exception_queue = Queue()
        Thread(target=get_valid_excpetions_thread, args=(exception_queue, email, key), daemon=True).start()
        exception_queues.append(exception_queue)

        downtime_queue = Queue()
        Thread(target=get_valid_downtimes_thread, args=(downtime_queue, email, key), daemon=True).start()
        downtime_queues.append(downtime_queue)

    if exclude is None:
        exclude = default_exclude_hosts
    if only is None:
        only = default_only_hosts

    node_list = []
    chal_list = []
    exception_list = []
    downtime_list = []
    for queue in node_queues:
        valid_nodes = queue.get()
        if valid_nodes is None:
            return None
        for node in valid_nodes:
            host_id = node.location[0]
            if only:
                if host_id in only:
                    node_list.append(node)
            else:
                if host_id not in exclude:
                    node_list.append(node)

    # challenge不能拿opened_only, 因为需要计算上次异常时间等。。
    for queue in chal_queues:
        valid_chals = queue.get()
        if valid_chals is None:
            return None
        for chal in valid_chals:
            host_id = chal.location[0]
            if only:
                if host_id in only:
                    chal_list.append(chal)
            else:
                if host_id not in exclude:
                    chal_list.append(chal)

    for queue in exception_queues:
        valid_exceptions = queue.get()
        if valid_exceptions is None:
            return None
        for ex in valid_exceptions:
            host_id = ex.location[0]
            if only:
                if host_id in only:
                    exception_list.append(ex)
            else:
                if host_id not in exclude:
                    exception_list.append(ex)

    for queue in downtime_queues:
        valid_downtimes = queue.get()
        if valid_downtimes is None:
            return None
        for downtime in valid_downtimes:
            host_id = downtime.location[0]
            if only:
                if host_id in only:
                    downtime_list.append(downtime)
            else:
                if host_id not in exclude:
                    downtime_list.append(downtime)
    return node_list, chal_list, exception_list, downtime_list

def restart_zend(host_id, node_id):
    try:
        logger.info('===> do restart_zend, host_id: {}, node_id: {}'.format(host_id, node_id))
        cmd = 'ssh z{} systemctl restart zen{}'.format(host_id, node_id)
        output = subprocess.check_output(cmd, shell=True)
        logger.info('===> restart_zend output: {}'.format(output))
    except subprocess.CalledProcessError:
        logger.warning('ssh failed, host_id: {}, node_id: {}'.format(host_id, node_id))

def snset(host_id, node_id, attr, value):
    try:
        logger.info('===> do snset, host_id: {}, node_id: {}, attr: {}, value: {}'.format(host_id, node_id, attr, value))
        cmd = 'ssh z{} snset {} {} {}'.format(host_id, node_id, attr, value)
        output = subprocess.check_output(cmd, shell=True)
        logger.info('===> snset output: {}'.format(output))
    except subprocess.CalledProcessError:
        logger.warning('ssh failed, host_id: {}, node_id: {}'.format(host_id, node_id))

def restart_secnode(host_id, node_id):
    try:
        logger.info('===> do restart_secnode, host_id: {}, node_id: {}'.format(host_id, node_id))
        cmd = 'ssh z{} systemctl restart secnode{}'.format(host_id, node_id)
        output = subprocess.check_output(cmd, shell=True)
        logger.info('===> restart_secnode output: {}'.format(output))
    except subprocess.CalledProcessError:
        logger.warning('ssh failed, host_id: {}, node_id: {}'.format(host_id, node_id))

def handle_downtime(node, dt):
    host_id, node_id = dt.location
    home = dt.home
    fqdn = dt.fqdn
    dtype = dt.dtype
    if dtype in default_ignore_dtype:
        logger.debug('downtime ignored, fqdn: {}, dtype: {}'.format(fqdn, dtype))
    else:
        logger.info('handle_downtime, node: {}, dt: {}'.format(node, dt))
        if dtype == 'sys':
            restart_secnode(host_id, node_id)
        elif dtype == 'zend':
            snset(host_id, node_id, 'home', home)
            restart_secnode(host_id, node_id)
        else:
            logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            logger.warning('downtime not handled: dt: {}'.format(dt))
            logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

def downtime_handler(queue):
    while True:
        node, dt = queue.get()
        handle_downtime(node, dt)

def handle_exception(node, ex):
    host_id, node_id = ex.location
    home = ex.home
    fqdn = ex.fqdn
    etype = ex.etype
    if etype in default_ignore_etype:
        logger.debug('exception ignored, fqdn: {}, etype: {}'.format(fqdn, etype))
    else:
        logger.info('handle_exception, node: {}, ex: {}'.format(node, ex))
        if etype == 'cert':
            restart_secnode(host_id, node_id)
        elif etype == 'peers':
            snset(host_id, node_id, 'home', home)
            restart_secnode(host_id, node_id)
        else:
            logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            logger.warning('exception not handled: ex: {}'.format(ex))
            logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

def exception_handler(queue):
    while True:
        node, ex = queue.get()
        handle_exception(node, ex)

def do_challenge(host_id, node_id, curserver=None):
    try:
        logger.info('===> do chanllenge, host_id: {}, node_id: {}'.format(host_id, node_id))
        # cmd = 'ssh z{} snchallenge {}'.format(host_id, node_id)
        if curserver is None:
            
            cmd = 'ssh z{} \'curl -s "https://$(snget {} home).zensystem.io/$(snget {} taddr)/$(snget {} nodeid)/send"\''.format(host_id, node_id, node_id, node_id)
        else:
            cmd = 'ssh z{} \'curl -s "https://{}.zensystem.io/$(snget {} taddr)/$(snget {} nodeid)/send"\''.format(host_id, curserver, node_id, node_id)
        print(cmd)
        output = subprocess.check_output(cmd, shell=True)
        logger.info('===> challenge output: {}, host_id: {}, node_id: {}'.format(output, host_id, node_id))
        
    except subprocess.CalledProcessError:
        logger.warning('ssh failed, host_id: {}, node_id: {}'.format(host_id, node_id))


def challenger(queue):
    while True:
        node = queue.get()
        host_id, node_id = node.location
        curserver = node.curserver
        do_challenge(host_id, node_id, curserver)
    
def check_chals(host_id, nodes, queue):
    logger.info('>>>>>>>>>>>>>>> check host: {} <<<<<<<<<<<<<<<'.format(host_id))
    now = int(time() * 1000)
    expected_min_duration = 30 * 60 * 1000  # 假设允许最小间隔为30分钟, 低于这个数就要调整
    predict_duration = (72 * 3600 + 600) * 1000  # 3天10分钟
    manual_challenge_duration = (71.5 * 3600) * 1000
    interval = 50 * 60 * 1000  # 50分钟, 保证最后一次挑战到now至少一个interval， 且now到最近的预期挑战也是至少一个interval

    not_pass_nodes = [node for node in nodes if not node.is_pass(ignore=True)]

    # 先处理overlap的情况(重启节点+重新挑战)
    for node in not_pass_nodes:
        if node.chals and node.chals[0].is_overlap():
            logger.info('[OVERLAP] host_id: {}, node: {}'.format(host_id, node))
            restart_secnode(host_id, node.id)
            sleep(1)
            queue.put(node)
            return

    if not_pass_nodes:
        logger.info('[ILLNESS] host {} NOT all pass'.format(host_id))
        for node in not_pass_nodes:
            node.dump()

        if len(not_pass_nodes) == 1:
            target_node = not_pass_nodes[0]
            # 必须没有exception或downtime
            if not target_node.is_no_exception_or_downtime(ignore=True):
                return


            # 取所有pass的节点的第一个有效挑战，排序
            valid_chal_nodes = [node for node in nodes if node not in not_pass_nodes and not node.exceptions and not node.downtimes and node.chals]
            sorted_nodes = sorted(valid_chal_nodes, key=lambda node: node.chals[0].receive_at)  # 从小到大
            if len(sorted_nodes) < 3:
                logger.debug('less than 3 sorted_nodes, ignored, sorted_nodes: {}, nodes: {}'.format(sorted_nodes, nodes))
                return

            durations = [(sorted_nodes[i+1].chals[0].start_at - sorted_nodes[i].chals[0].receive_at) for i in range(0, len(sorted_nodes) - 1)]
            min_duration = min(durations)

            last_chal_receive_at = sorted_nodes[-1].chals[0].receive_at
            nearest_predict_chal_start_at = now
            for node in sorted_nodes:
                predict_start_at = node.chals[0].receive_at + predict_duration
                if predict_start_at < now - 20 * 60 * 1000:
                    # 某些节点挑战间隔超过3天, 忽略这些节点
                    continue
                else:
                    nearest_predict_chal_start_at  = predict_start_at
                    break

            if (last_chal_receive_at + interval) < now < (nearest_predict_chal_start_at - interval):
                logger.info('[OK] host {} start challenge, node: {}'.format(host_id, target_node))
                queue.put(target_node)
    
            else:
                logger.info('[GOOD] host {} wait for appropriate time to challenge, min_duration: {}'.format(host_id, min_duration))
            
    else:
        # 取每个节点的第一个有效挑战，排序
        valid_chal_nodes = [node for node in nodes if not node.exceptions and not node.downtimes and node.chals]
        sorted_nodes = sorted(valid_chal_nodes, key=lambda node: node.chals[0].receive_at)  # 从小到大

        # 如果小于3个节点，无需处理, #TODO
        if len(sorted_nodes) < 3:
            logger.debug('less than 3 sorted_nodes, ignored, sorted_nodes: {}, nodes: {}'.format(sorted_nodes, nodes))
            return

        durations = [(sorted_nodes[i+1].chals[0].start_at - sorted_nodes[i].chals[0].receive_at) for i in range(0, len(sorted_nodes) - 1)]
        min_duration = min(durations)

        index = durations.index(min_duration)  # durations的index映射到sorted_chals

        # logger.debug('min_duration: {}, expected_min_duration: {}'.format(min_duration, expected_min_duration))
        if min_duration < expected_min_duration:
            target_node = sorted_nodes[index]
            target_node_after = sorted_nodes[index+1]

            last_chal_receive_at = sorted_nodes[-1].chals[0].receive_at
            nearest_predict_chal_start_at = now
            for node in sorted_nodes:
                predict_start_at = node.chals[0].receive_at + predict_duration
                if predict_start_at < now - 20 * 60 * 1000:
                    # 某些节点挑战间隔超过3天, 忽略这些节点
                    continue
                else:
                    nearest_predict_chal_start_at  = predict_start_at
                    break

            if (last_chal_receive_at + interval) < now < (nearest_predict_chal_start_at - interval):
                logger.info('[OK] host {} start challenge, node: {}'.format(host_id, target_node))
                queue.put(target_node)
            else:
                logger.info('[GOOD] host {} wait for appropriate time to challenge, min_duration: {}'.format(host_id, min_duration))
        else:
            logger.info('[PERFECT] host {} is healthy, min_duration: {}'.format(host_id, min_duration))
            # 完全perfect时，选择合适的时间主动发起挑战
            first_chal_receive_at = sorted_nodes[0].chals[0].receive_at
            last_chal_receive_at = sorted_nodes[-1].chals[0].receive_at
            if last_chal_receive_at < now - interval and now > first_chal_receive_at + manual_challenge_duration:
                first_node = sorted_nodes[0]
                logger.info('[PERFECT] manually challenge on host {}, node: {}'.format(host_id, first_node))
                queue.put(first_node)


def check():
    exception_handler_queue = Queue()
    downtime_handler_queue = Queue()
    challenge_handler_queue = Queue()

    thread_list = []
    t = Thread(target=exception_handler, args=(exception_handler_queue,), daemon=True)
    t.start()
    thread_list.append(t)
    t = Thread(target=downtime_handler, args=(downtime_handler_queue,), daemon=True)
    t.start()
    thread_list.append(t)
    t = Thread(target=challenger, args=(challenge_handler_queue,), daemon=True)
    t.start()
    thread_list.append(t)

    while True:
        logger.info('----------------------------------------------------------------------------------------')
        everything = get_everything()
        if everything is None:
            logger.warning('everything is None')
            sleep(10)
            continue
        node_list, chal_list, exception_list, downtime_list = everything

        node_dict_by_host = defaultdict(lambda: [])
        node_dict = {}
        for node in node_list:
            node_dict[node.fqdn] = node
        host_id, node_id = node.location
        node_dict_by_host[host_id].append(node)

        for chal in chal_list:
            node = node_dict[chal.fqdn]
            node.chals.append(chal)

        for fqdn, node in node_dict.items():
            node_dict

        for ex in exception_list:
            node = node_dict[ex.fqdn]
            node.exceptions.append(ex)
            if ex.duration > 15 * 60 * 1000:
                exception_handler_queue.put((node, ex))

        for dt in downtime_list:
            node = node_dict[dt.fqdn]
            node.downtimes.append(dt)
            if dt.duration > 15 * 60 * 1000:
                downtime_handler_queue.put((node, dt))

        for host_id, nodes in node_dict_by_host.items():
            for node in nodes:
                chals = node.chals
                node.chals = sorted(chals, key=lambda chal:chal.start_at, reverse=True)
                exceptions = node.exceptions
                node.exceptions = sorted(exceptions, key=lambda ex:ex.start_at, reverse=True)
                downtimes = node.downtimes
                node.downtimes = sorted(downtimes, key=lambda dt:dt.start_at, reverse=True)

            check_chals(host_id, nodes, challenge_handler_queue)

        sleep(600)


class Monitor:
    def __init__(self):
        self.exceptions_dict = defaultdict(lambda: {})
        self.downtimes_dict = defaultdict(lambda: {})
        self.nodes_dict = defaultdict(lambda: {})
        self.chals_dict = defaultdict(lambda: {})
        self.servers_status_dict = defaultdict(lambda : {})
        self.servers = [
            'ts1.eu', 'ts2.eu', 'ts3.eu', 'ts4.eu',
            'ts1.na', 'ts2.na', 'ts3.na', 'ts4.na',
        ]
        self.server_open_chal_dict = {}

    def check_server_thread(self, server_name):
        while True:
            try:
                r = requests.get('https://{server_name}.zensystem.io/api/srvstats'.format(server_name=server_name))
                now = int(time() * 1000)
                self.servers_status_dict[server_name]['result'] = r.status_code
                self.servers_status_dict[server_name]['timestamp'] = now
                sleep(20)
            except:
                sleep(10)

    def check_server_open_chal_thread(self):
        while True:
            try:
                response = requests.get('https://securenodes.eu.zensystem.io/api/chal/open')
                resp = response.json()
                now = int(time() * 1000)
                chalOpenCount = resp['chalOpenCount']
                open_chal_dict = {}
                for entry in chalOpenCount:
                    server = entry['server']
                    count = entry['count']
                    open_chal_dict[server] = int(count)
                    
                self.server_open_chal_dict = open_chal_dict

                sleep(20)
            except:
                sleep(10)

    def get_valid_excpetions_thread(self, email, key, opened_only=True):
        while True:
            try:
                valid_excpetions = get_valid_exceptions(email, key, opened_only=opened_only)
                now = int(time() * 1000)
                self.exceptions_dict[key]['result'] = valid_excpetions
                self.exceptions_dict[key]['timestamp'] = now
                sleep(60)
            except:
                sleep(20)

    def get_valid_downtimes_thread(self, email, key, opened_only=True):
        while True:
            try:
                valid_downtimes = get_valid_downtimes(email, key, opened_only=opened_only)
                now = int(time() * 1000)
                self.downtimes_dict[key]['result'] = valid_downtimes
                self.downtimes_dict[key]['timestamp'] = now
                sleep(60)
            except:
                sleep(20)

    def get_valid_nodes_thread(self, email, key):
        while True:
            try:
                valid_nodes = get_valid_nodes(email, key)
                now = int(time() * 1000)
                self.nodes_dict[key]['result'] = valid_nodes
                self.nodes_dict[key]['timestamp'] = now
                sleep(60)
            except:
                sleep(20)

    def get_valid_chals_thread(self, email, key):
        while True:
            try:
                valid_chals = get_valid_chals(email, key)
                now = int(time() * 1000)
                self.chals_dict[key]['result'] = valid_chals
                self.chals_dict[key]['timestamp'] = now
                sleep(60)
            except:
                sleep(20)

    def validate_server(self, server):
        if self.servers_status_dict[server]['result'] == 200:
            return True
        else:
            logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            logger.warning('server down, server: {}'.format(server))
            logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            return False
        

    def challenger(self, queue):
        while True:
            node = queue.get()
            host_id, node_id = node.location
            curserver = node.curserver
            if curserver not in self.server_open_chal_dict:
                logger.warning('server {} in maintenance, can NOT challenge'.format(curserver))
                continue

            if self.validate_server(curserver):
                do_challenge(host_id, node_id, curserver)

    def handle_downtime(self, node, dt):
        host_id, node_id = dt.location
        node_home = node.home
        dt_home = dt.home
        node_curserver = node.curserver
        dt_curserver = dt.curserver
        fqdn = dt.fqdn
        dtype = dt.dtype
        if dtype in default_ignore_dtype:
            logger.debug('downtime ignored, fqdn: {}, dtype: {}'.format(fqdn, dtype))
        else:
            logger.info('handle_downtime, node: {}, dt: {}'.format(node, dt))

            if node_home != dt_home or node_curserver != dt_curserver:
                logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logger.warning('downtime home or curserver not equal')
                logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

            if dtype == 'sys':
                if self.validate_server(dt_curserver):
                    snset(host_id, node_id, 'home', dt_curserver)
                restart_secnode(host_id, node_id)
            elif dtype == 'zend':
                if self.validate_server(dt_curserver):
                    snset(host_id, node_id, 'home', dt_curserver)
                restart_secnode(host_id, node_id)
            else:
                logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logger.warning('downtime not handled: dt: {}'.format(dt))
                logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

    def downtime_handler(self, queue):
        while True:
            node, dt = queue.get()
            self.handle_downtime(node, dt)

    def handle_exception(self, node, ex):
        host_id, node_id = ex.location
        node_home = node.home
        ex_home = ex.home
        fqdn = ex.fqdn
        etype = ex.etype
        if etype in default_ignore_etype:
            logger.debug('exception ignored, fqdn: {}, etype: {}'.format(fqdn, etype))
        else:
            logger.info('handle_exception, node: {}, ex: {}'.format(node, ex))
            if node_home != ex_home:
                logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logger.warning('ex home not equal')
                logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            if etype == 'cert':
                restart_secnode(host_id, node_id)
            elif etype == 'peers':
                if self.validate_server(ex_home):
                    snset(host_id, node_id, 'home', ex_home)
                restart_secnode(host_id, node_id)
            # elif etype == 'chal':
            #     if self.validate_server(ex_home):
            #         snset(host_id, node_id, 'home', ex_home)
            #     restart_secnode(host_id, node_id)
            else:
                logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logger.warning('exception not handled: ex: {}'.format(ex))
                logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')

    def exception_handler(self, queue):
        while True:
            node, ex = queue.get()
            self.handle_exception(node, ex)

    def check_chals(self, host_id, nodes, queue):
        logger.info('>>>>>>>>>>>>>>> check host: {} <<<<<<<<<<<<<<<'.format(host_id))
        now = int(time() * 1000)
        expected_min_duration = 30 * 60 * 1000  # 假设允许最小间隔为30分钟, 低于这个数就要调整
        predict_duration = (72 * 3600 + 600) * 1000  # 3天10分钟
        manual_challenge_duration = (71.5 * 3600) * 1000
        interval = 50 * 60 * 1000  # 50分钟, 保证最后一次挑战到now至少一个interval， 且now到最近的预期挑战也是至少一个interval

        not_pass_nodes = [node for node in nodes if not node.is_pass(ignore=True)]

        # 先处理overlap的情况(重启节点+重新挑战)
        for node in not_pass_nodes:
            if node.chals and node.chals[0].is_overlap():
                logger.info('[OVERLAP] host_id: {}, node: {}'.format(host_id, node))
                restart_secnode(host_id, node.id)
                sleep(1)
                queue.put(node)
                return

        if not_pass_nodes:
            logger.info('[ILLNESS] host {} NOT all pass'.format(host_id))
            for node in not_pass_nodes:
                node.dump()

            if len(not_pass_nodes) == 1:
                target_node = not_pass_nodes[0]
                # 必须没有exception或downtime
                if not target_node.is_no_exception_or_downtime(ignore=True):
                    return

                # 取所有pass的节点的第一个有效挑战，排序
                valid_chal_nodes = [node for node in nodes if
                                    node not in not_pass_nodes and not node.exceptions and not node.downtimes and node.chals]
                sorted_nodes = sorted(valid_chal_nodes, key=lambda node: node.chals[0].receive_at)  # 从小到大
                if len(sorted_nodes) < 3:
                    logger.debug(
                        'less than 3 sorted_nodes, ignored, sorted_nodes: {}, nodes: {}'.format(sorted_nodes, nodes))
                    return

                durations = [(sorted_nodes[i + 1].chals[0].start_at - sorted_nodes[i].chals[0].receive_at) for i in
                             range(0, len(sorted_nodes) - 1)]
                min_duration = min(durations)

                last_chal_receive_at = sorted_nodes[-1].chals[0].receive_at
                nearest_predict_chal_start_at = now
                for node in sorted_nodes:
                    predict_start_at = node.chals[0].receive_at + predict_duration
                    if predict_start_at < now - 20 * 60 * 1000:
                        # 某些节点挑战间隔超过3天, 忽略这些节点
                        continue
                    else:
                        nearest_predict_chal_start_at = predict_start_at
                        break

                if (last_chal_receive_at + interval) < now < (nearest_predict_chal_start_at - interval):
                    logger.info('[OK] host {} start challenge, node: {}'.format(host_id, target_node))
                    queue.put(target_node)

                else:
                    logger.info(
                        '[GOOD] host {} wait for appropriate time to challenge, min_duration: {}'.format(host_id, min_duration))

        else:
            # 取每个节点的第一个有效挑战，排序
            valid_chal_nodes = [node for node in nodes if not node.exceptions and not node.downtimes and node.chals]
            sorted_nodes = sorted(valid_chal_nodes, key=lambda node: node.chals[0].receive_at)  # 从小到大

            # 如果小于3个节点，无需处理, #TODO
            if len(sorted_nodes) < 3:
                logger.debug(
                    'less than 3 sorted_nodes, ignored, sorted_nodes: {}, nodes: {}'.format(sorted_nodes, nodes))
                return

            durations = [(sorted_nodes[i + 1].chals[0].start_at - sorted_nodes[i].chals[0].receive_at) for i in
                         range(0, len(sorted_nodes) - 1)]
            min_duration = min(durations)

            index = durations.index(min_duration)  # durations的index映射到sorted_chals

            # logger.debug('min_duration: {}, expected_min_duration: {}'.format(min_duration, expected_min_duration))
            if min_duration < expected_min_duration:
                target_node = sorted_nodes[index]
                target_node_after = sorted_nodes[index + 1]

                last_chal_receive_at = sorted_nodes[-1].chals[0].receive_at
                nearest_predict_chal_start_at = now
                for node in sorted_nodes:
                    predict_start_at = node.chals[0].receive_at + predict_duration
                    if predict_start_at < now - 20 * 60 * 1000:
                        # 某些节点挑战间隔超过3天, 忽略这些节点
                        continue
                    else:
                        nearest_predict_chal_start_at = predict_start_at
                        break

                if (last_chal_receive_at + interval) < now < (nearest_predict_chal_start_at - interval):
                    logger.info('[OK] host {} start challenge, node: {}'.format(host_id, target_node))
                    queue.put(target_node)
                else:
                    logger.info(
                        '[GOOD] host {} wait for appropriate time to challenge, min_duration: {}'.format(host_id,
                                                                                                         min_duration))
            else:
                logger.info('[PERFECT] host {} is healthy, min_duration: {}'.format(host_id, min_duration))
                # 完全perfect时，选择合适的时间主动发起挑战
                first_chal_receive_at = sorted_nodes[0].chals[0].receive_at
                last_chal_receive_at = sorted_nodes[-1].chals[0].receive_at
                if last_chal_receive_at < now - interval and now > first_chal_receive_at + manual_challenge_duration:
                    first_node = sorted_nodes[0]
                    logger.info('[PERFECT] manually challenge on host {}, node: {}'.format(host_id, first_node))
                    queue.put(first_node)

    def main_loop(self, exclude=None, only=None):
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)10s:%(lineno)-4s - %(levelname)-5s %(message)s')
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        thread_list = []
        for email, key in apikeys.items():
            t = Thread(
                target=self.get_valid_excpetions_thread,
                args=(email, key),
                daemon=True,
            )
            t.start()
            thread_list.append(t)

            t = Thread(
                target=self.get_valid_downtimes_thread,
                args=(email, key),
                daemon=True,
            )
            t.start()
            thread_list.append(t)

            t = Thread(
                target=self.get_valid_nodes_thread,
                args=(email, key),
                daemon=True,
            )
            t.start()
            thread_list.append(t)

            t = Thread(
                target=self.get_valid_chals_thread,
                args=(email, key),
                daemon=True,
            )
            t.start()
            thread_list.append(t)

        t = Thread(
            target=self.check_server_open_chal_thread,
            daemon=True,
        )
        t.start()
        thread_list.append(t)

        for server in self.servers:
            t = Thread(
                target=self.check_server_thread,
                args=(server, ),
                daemon=True,
            )
            t.start()
            thread_list.append(t)

        exception_handler_queue = Queue()
        downtime_handler_queue = Queue()
        challenge_handler_queue = Queue()

        thread_list = []
        t = Thread(target=self.exception_handler, args=(exception_handler_queue,), daemon=True)
        t.start()
        thread_list.append(t)
        t = Thread(target=self.downtime_handler, args=(downtime_handler_queue,), daemon=True)
        t.start()
        thread_list.append(t)
        t = Thread(target=self.challenger, args=(challenge_handler_queue,), daemon=True)
        t.start()
        thread_list.append(t)

        sleep(3)  # wait for status collection

        if exclude is None:
            exclude = default_exclude_hosts
        if only is None:
            only = default_only_hosts

        while True:
            exception_list = []
            downtime_list = []
            chal_list = []
            node_list = []
            down_server_list = []
            now = int(time()*1000)

            server_status_ready = True
            for server in self.servers:
                if server not in self.servers_status_dict:
                    logger.warning('server not available in servers_status_dict')
                    server_status_ready = False
                    break
                status_timestamp = self.servers_status_dict[server]['timestamp']
                if now - status_timestamp > 200000:
                    logger.warning('status_timestamp out of date, server: {}'.format(server))
                    server_status_ready = False
                    break
                else:
                    status_code = self.servers_status_dict[server]['result']
                    if status_code == 200:
                        pass
                    elif status_code == 502:
                        down_server_list.append(server)
                    elif status_code == 521:
                        down_server_list.append(server)
                    else:
                        logger.warning('!!!!!!!!!!!!!!!!!!!!!!!')
                        logger.warning('status_code unexpected, status_code: '.format(status_code))
                        logger.warning('!!!!!!!!!!!!!!!!!!!!!!!')
                        down_server_list.append(server)

            if not server_status_ready:
                sleep(10)
                continue

            everything_ready = True
            for email, key in apikeys.items():
                if key not in self.exceptions_dict:
                    logger.warning('key not available in exceptions_dict, email: {}, key: {}'.format(email, key))
                    everything_ready = False
                    continue
                exceptions_timestamp = self.exceptions_dict[key]['timestamp']
                if now - exceptions_timestamp > 200000:
                    logger.warning('exceptions_timestamp out of date, key: {}'.format(key))
                    everything_ready = False
                    break
                else:
                    valid_exceptions = self.exceptions_dict[key]['result']
                    for ex in valid_exceptions:
                        host_id = ex.location[0]
                        if only:
                            if host_id in only:
                                exception_list.append(ex)
                        else:
                            if host_id not in exclude:
                                exception_list.append(ex)

                if key not in self.downtimes_dict:
                    logger.warning('key not available in downtimes_dict, email: {}, key: {}'.format(email, key))
                    everything_ready = False
                    continue
                downtimes_timestamp = self.downtimes_dict[key]['timestamp']
                if now - downtimes_timestamp > 200000:
                    logger.warning('downtimes_timestamp out of date, key: {}'.format(key))
                    everything_ready = False
                    break
                else:
                    valid_downtimes = self.downtimes_dict[key]['result']
                    for dt in valid_downtimes:
                        host_id = dt.location[0]
                        if only:
                            if host_id in only:
                                downtime_list.append(dt)
                        else:
                            if host_id not in exclude:
                                downtime_list.append(dt)

                if key not in self.nodes_dict:
                    logger.warning('key not available in nodes_dict, email: {}, key: {}'.format(email, key))
                    everything_ready = False
                    continue
                nodes_timestamp = self.nodes_dict[key]['timestamp']
                if now - nodes_timestamp > 200000:
                    logger.warning('downtimes_timestamp out of date, key: {}'.format(key))
                    everything_ready = False
                    break
                else:
                    valid_nodes = self.nodes_dict[key]['result']
                    for node in valid_nodes:
                        host_id = node.location[0]
                        if only:
                            if host_id in only:
                                node_list.append(node)
                        else:
                            if host_id not in exclude:
                                node_list.append(node)

                if key not in self.chals_dict:
                    logger.warning('key not available in chals_dict, email: {}, key: {}'.format(email, key))
                    everything_ready = False
                    continue
                chals_timstamp = self.chals_dict[key]['timestamp']
                if now - chals_timstamp > 200000:
                    logger.warning('chals_timestamp out of date, key: {}'.format(key))
                    everything_ready = False
                    break
                else:
                    valid_chals = self.chals_dict[key]['result']
                    for chal in valid_chals:
                        host_id = chal.location[0]
                        if only:
                            if host_id in only:
                                chal_list.append(chal)
                        else:
                            if host_id not in exclude:
                                chal_list.append(chal)

            if not everything_ready:
                sleep(10)
                continue

            if down_server_list:
                logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                logger.warning('SERVER DOWN, down_server_list: {}'.format(down_server_list))
                logger.warning('!!!!!!!!!!!!!!!!!!!!!!!!!!!')
                #sleep(300)
                #continue

            node_dict_by_host = defaultdict(lambda: [])
            node_dict = {}
            for node in node_list:
                node_dict[node.fqdn] = node
                host_id, node_id = node.location
                node_dict_by_host[host_id].append(node)

            for chal in chal_list:
                fqdn = chal.fqdn
                if fqdn in node_dict:
                    node = node_dict[fqdn]
                    node.chals.append(chal)

            for ex in exception_list:
                fqdn = ex.fqdn
                if fqdn in node_dict:
                    node = node_dict[fqdn]
                    node.exceptions.append(ex)
                    if ex.duration > 12 * 60 * 1000 or now - ex.check_at > 12 * 60 * 1000:
                        exception_handler_queue.put((node, ex))

            for dt in downtime_list:
                fqdn = dt.fqdn
                if fqdn in node_dict:
                    node = node_dict[fqdn]
                    node.downtimes.append(dt)
                    home_ne_curserver_over_5m = dt.home != dt.curserver and (dt.duration > 5 * 60 * 1000 or now - dt.check_at > 5 * 60 * 1000)
                    over_12m = dt.duration > 12 * 60 * 1000 or now - dt.check_at > 12 * 60 * 1000
                    if home_ne_curserver_over_5m or over_12m:
                        downtime_handler_queue.put((node, dt))


            for host_id, nodes in node_dict_by_host.items():
                for node in nodes:
                    chals = node.chals
                    node.chals = sorted(chals, key=lambda chal:chal.start_at, reverse=True)
                    exceptions = node.exceptions
                    node.exceptions = sorted(exceptions, key=lambda ex:ex.start_at, reverse=True)
                    downtimes = node.downtimes
                    node.downtimes = sorted(downtimes, key=lambda dt:dt.start_at, reverse=True)

                self.check_chals(host_id, nodes, challenge_handler_queue)

            sleep(8 * 60)

#
# 测试函数
#
def test_chals():    
    chals_dict = get_all_chals()
    fqdn_list = chals_dict.keys()
    print(fqdn_list)
    print(len(fqdn_list))

def test_downtimes():    
    downtimes_dict = get_all_downtimes()
    fqdn_list = downtimes_dict.keys()
    print(fqdn_list)
    print(len(fqdn_list))


def print_nodes_by_hosts():    
    nodes_dict = get_all_nodes_by_host()
    for host_id, nodes in nodes_dict.items():
        print(host_id)
        for node in nodes:
            print(node)

def test_nodes_chals():
    nodes_dict = get_all_nodes_by_host()
    chals_dict = get_all_chals()
    for host_id, nodes in nodes_dict.items():
        print()
        print('------------------------------------------------------- {} ------------------------------------------------------'.format(host_id))
        print()
        for node in nodes:
            
            chals = chals_dict[node.fqdn]
            print(node)
            for chal in chals:
                print(chal)
            print()


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(filename)10s:%(lineno)-4s - %(levelname)-5s %(message)s')
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    check()
               

if __name__ == '__main__':
    #test()
    main()

