import re
import os
import sys
#import urllib2
import telnetlib
import time
import threading
from Queue import PriorityQueue

TIMEOUT = 180
THREAD_COUNT = 10
HOST_FILE = 'E:\workspace\CheckGoogleHost\host_file.txt'

def load_host_file(host_file):
    if not os.path.exists(host_file):
        return None

    new_file = host_file + '.new'
    
    if os.path.exists(new_file):
       host_file = new_file

    result_hosts = []
    parse_host_file(host_file, result_hosts)

    print result_hosts
    if len(result_hosts):
        write_hosts(new_file, result_hosts)

    return result_hosts


def parse_host_file(host_file, result_hosts):
    with open(host_file, 'r') as f:
        for line in f.readlines():
            tmp_hosts = [h.strip() for h in line[:-1].split(' ')]
            hosts = check_host_format(tmp_hosts)

            if len(hosts):
                result_hosts.extend(hosts)

            #print '%s effective host %d' % (host_file, host_count)


def write_hosts(savefile, hosts):

    with open(savefile, 'w') as f:
        for host in hosts:
            f.write('%s\n' % (host))



def check_host_format(hosts):
    results = []
    pattern = re.compile('(\d{1,3}\.){3}\d{1,3}')

    for i in range(len(hosts)):
        if not pattern.match(hosts[i]):
            continue
        results.append(hosts[i])

    return results


class HostInfo:
    def __init__(self, host, max_):
        self.host = host
        self.cost = max_

    def set_cost(self, cost):
        self.cost = cost

    def __lt__(self, right):
        return self.cost < right.cost


class CheckHandler(threading.Thread):
    def __init__(self, thread_id, timeout):
        threading.Thread.__init__(self)
        self.id = thread_id
        self.timeout = timeout
        self.hosts = []
        self.results = []

    def run(self):
        for host in self.hosts:
            cost = self.check_host_time(host)
            if cost < self.timeout:
                self.results.append(HostInfo(host, cost))


    def add_hosts(self, host):
        self.hosts.append(host)

    def get_results(self):
        return self.results


    def check_host_time(self, host):
        '''
        url = 'http://%s' % (host)
        cost = self.timeout
        try:
            begin = time.time()
            urllib2.urlopen(url, timeout=self.timeout)
            end = time.time()

            cost = int((end - begin) * 1000)

        except urllib2.URLError, e:
            print '%s timeout, e is %s' % (host, str(e))

        except Exception, e:
            print '%s check host error %s' % (host, e)
        '''

        cost = self.timeout
        try:
            begin = time.time()
            tn = telnetlib.Telnet(host, 80, self.timeout)
            end = time.time()

            cost = int((end - begin) * 1000)

        except Exception, e:
            print '%s timeout, e is %s' % (host, str(e))

        return cost


def main():
    main_begin = time.time()
    global TIMEOUT, THREAD_COUNT
    hosts = []
    '''
	for i in len(sys.argv):
		if not i:
			hosts.expend(load_host_file(sys.argv[i]))
	'''
    global HOST_FILE
    hosts.extend(load_host_file(HOST_FILE))

    count = len(hosts) / THREAD_COUNT
    thread_manager = []
    for i in range(count):
        t = CheckHandler(i, TIMEOUT)
        thread_manager.append(t)

    for i in range(len(hosts)):
        if not hosts[i]: continue
        n = i % count
        thread_manager[n].add_hosts(hosts[i])

    for t in thread_manager:
        t.start()
        time.sleep(0.1)

    for t in thread_manager:
        t.join()

    print 'all threads over'

    print len(thread_manager)

    pq = PriorityQueue(maxsize=100000)
    for t in thread_manager:
        for hi in t.get_results():
            pq.put(hi)

    for i in range(10):
        host_info = pq.get()
        print 'host: %s,  cost: %sms' % (host_info.host, host_info.cost)

    main_end = time.time()
    print 'main function cost: %dms' % (int((main_end - main_begin)*1000))

if __name__ == '__main__':
    main()


