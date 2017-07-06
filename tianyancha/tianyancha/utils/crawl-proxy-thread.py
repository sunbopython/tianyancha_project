#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import re
import requests
import copy
import threading
try:
    from Queue import Queue
except:
    from queue import Queue
import time
from parsel import Selector



def parse_args():
    parser = argparse.ArgumentParser(description="Get proxy from 'http://gatherproxy.com/'")
    parser.add_argument("-c","--country",help="Get proxy from specified country")
    parser.add_argument("-r","--reverse",action="store_true",help="Get proxy except specified country")
    parser.add_argument("--maxpage",type=int,default=10,help="max page number of 'http://gatherproxy.com'")
    parser.add_argument("--checknum",type=int,default=3,help="checking times for every proxy")
    parser.add_argument("--checkthreshold",type=float,default=0.6,help="threshold for successful request percentage")
    parser.add_argument("--timeout",type=int,default=15,help="timeout of request")
    args = parser.parse_args()
    return args

class find_http_proxy():
    """ find proxy from "http://gatherproxy.com/"(needs proxy to visit in China)

        Will only gather L1 (elite anonymity) proxies which should not 
        give out your IP or advertise that you are using a proxy at all.


        Attributes:
            proy_file: A txt which would save a list of valid proxy 
            country: find specified country proxy
            reverse:  filter opposite country proxy
            checknum: checking times for every proxy
            checkthreshold: threshold for successful request percentage
            proxy_list: A list consist of proxy and port 
            headers: A default user-agent setting

    """
     
    #def __init__(self,country=None,reverse=False):
    def __init__(self,args):
        self.country = args.country     
        self.reverse = args.reverse if self.country else None
        self.maxpage = args.maxpage
        self.checknum = args.checknum
        self.checkthreshold = args.checkthreshold
        self.timeout = args.timeout
        self.proxy_list = []
        self.headers = {
                'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.154 Safari/537.36',
                'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        

    def getherproxy_req(self):
        """get proxy from gatherproxy.com
        """
        url = 'http://gatherproxy.com/proxylist/anonymity/?t=Elite'
        for pagenum in range(1,self.maxpage+1):
            try:
                data = {'Type':'elite','PageIdx':str(pagenum),'Uptime':'0'}
                headers = copy.copy(self.headers)
                r = requests.post(url, headers=headers, data=data) 
            except Exception as e:
                print(str(e))
                print('[!] Failed: %s' % url)
                gatherproxy_list = []
                return gatherproxy_list
            self._get_proxy(r.text,country=self.country)
        print("[+] Finished getting proxy: {}".format(len(self.proxy_list)))

    def _get_proxy(self,html,country):
        """Parse the raw html into proxy list

            Args:
                html: web html string
                country: filter proxy by country name

            Return:
                A list consists of proxy-port and contry
                example:

                ['192.168.45.22:80,China',
                '92.28.45.22:80,HONG KONG',
                '52.40.56.35,United States'
                ...]

        """
        sels = Selector(text=html)
        for index,sel in enumerate(sels.xpath("//div[contains(@class,'proxy-list')]/table/tr")):
            if index>=2:   # ignore table head and other stuff
                if country:
                    proxy_temp = "{}:{},{}".format(
                                    sel.xpath('td[2]').re(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')[0],
                                    str(int(sel.xpath('td[3]').re(r"dep\('(.+)'\)")[0], 16)),
                                    sel.xpath('td[5]/text()').extract()[0]
                                    )
                    #print(proxy_temp)
                    if self.reverse:
                        proxy_info = proxy_temp.split(',')[0] if proxy_temp.split(',')[1]!=country else None 
                    else:
                        proxy_info = proxy_temp.split(',')[0] if proxy_temp.split(',')[1]==country else None 
                else:
                    proxy_info = "{}:{}".format(
                                    sel.xpath('td[2]').re(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')[0],
                                    str(int(sel.xpath('td[3]').re(r"dep\('(.+)'\)")[0], 16))
                                    )

                if proxy_info:
                    self.proxy_list.append(proxy_info) 

    
    def proxy_checker(self,proxy):
        """ Further test for proxy

        Argus:
            proxy: Web proxy with port in following format:'189.28.188.89:80'
            test_url: An url that we have known the text content within it
            check_string: The target checing string in test_url

        Return:
            A boolen value, true stands for passing test, false stands the reverse
 
        """

        test_url = 'http://myip.dnsdynamic.org'
        check_string = proxy.split(":")[0]  #which is proxy itself
        proxydict={'http':'http://'+proxy}
        count = 0
        
        for times in range(self.checknum):
            try:
                r = requests.get(test_url,proxies=proxydict,timeout=self.timeout)
                if r.status_code == 200 and check_string in r.text: 
                    count = count + 1       
            except Exception as e:
                pass
        if count/self.checknum>=self.checkthreshold:
            print(proxy)
            return True
            
           
if __name__ == '__main__':
    """ crawl proxy without stop, but rests certain seconds after every time
    """
    findProxy = find_http_proxy(parse_args())
    #findProxy = find_http_proxy(country="China",reverse=True)
    print("starting...")
    findProxy.getherproxy_req()

    list_lock = threading.Lock()
    newList = []
    start = time.time()

    def saveproxy():
        with open("validProxy.txt",'w') as fd:
            for proxy in newList:
                fd.write(proxy+"\n")
            
    def worker():
        while True:
            proxy = q.get()
            check_proxy(proxy)
            q.task_done()

    def check_proxy(proxy):
        proxybool = findProxy.proxy_checker(proxy)
        with list_lock:
            if proxybool:
                newList.append(proxy)

    q = Queue()
    num_worker_threads = 30  # or 30
    for i in range(num_worker_threads):
        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    for proxy in findProxy.proxy_list:
        q.put(proxy)

    q.join()
    saveproxy()
    print("length of successful proxy is %d" % len(newList))
    print("finished writing to validProxy.txt")
    print("Entire job took: %s" % (time.time()-start))