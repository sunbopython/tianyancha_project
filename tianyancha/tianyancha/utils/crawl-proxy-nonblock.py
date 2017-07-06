#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import re
import requests
import copy
import time
from parsel import Selector
from twisted.internet import reactor
from twisted.web import client


from scrapy.http import Request,FormRequest
from scrapy.core.downloader.handlers.http11 import HTTP11DownloadHandler
from scrapy.settings import Settings
from twisted.internet import reactor,defer,task



def parse_args():
    parser = argparse.ArgumentParser(description="Get proxy from 'http://gatherproxy.com/'")
    group0=parser.add_argument_group('common')
    group0.add_argument("--conc",help="concurrent numbers",type=int,default=8)
    group0.add_argument("--timeout",type=int,default=15,help="timeout of request")

    group1=parser.add_argument_group('Proxy get')
    group1.add_argument("--country",help="Get proxy from specified country")
    group1.add_argument("--reverse",action="store_true",help="Get proxy except specified country")
    group1.add_argument("--maxpage",type=int,default=10,help="max page number of 'http://gatherproxy.com'")

    group2 = parser.add_argument_group('Proxy check')
    group2.add_argument("--checknum",type=int,default=3,help="checking times for every proxy")
    group2.add_argument("--checkthreshold",type=float,default=0.6,help="threshold for successful request percentage")
    args = parser.parse_args()
    return args

class find_http_proxy():
    """ find elite proxy from "http://gatherproxy.com/"(needs proxy to visit in China)

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
     
    def __init__(self,args):
        self.concurrent = args.conc
        self.country = args.country     
        self.reverse = args.reverse if self.country else None
        self.maxpage = args.maxpage
        self.checknum = args.checknum
        self.checkthreshold = args.checkthreshold
        self.timeout = args.timeout
        self.proxy_list = []
        self.passproxy = set()  # records proxy which conforms to the condition: successful rate above some level     
        self.headers = {'USER-AGENT':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.154 Safari/537.36'}
        

    def getherproxy_req(self):
        """get proxy from gatherproxy.com"""
        block = True
        
        if not block:
            # method1-nonblock
            url = 'http://gatherproxy.com/proxylist/anonymity/?t=Elite'
            settings = Settings()
            @defer.inlineCallbacks
            def getpage(request,page):
                try:
                    print("Request {},pagenumber:{}".format(request,page))
                    response = yield HTTP11DownloadHandler(settings).download_request(request,spider=None)
                    if response.status==200:
                        self._get_proxy(response.body.decode(),country=self.country)
                except Exception as e:
                    print(e)
                    print("[!] Failed: request {} of page:{}".format(request,page))
                    pass##
            def iter_page():
                work =( 
                            getpage(FormRequest(url=url,
                                                headers=self.headers,
                                                formdata={'Type':'elite','PageIdx':str(page),'Uptime':'0'},
                                                meta={'download_timeout':60}),page=page)  for page in range(1,self.maxpage+1)
                        )
                coop = task.Cooperator()
                join = defer.DeferredList(coop.coiterate(work) for i in range(self.concurrent))
                join.addBoth(lambda _: reactor.stop())
            iter_page()
            reactor.run()
        else:
            # method 2- block
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

    
    def proxy_checker(self):
        """ Further test for proxy"""
        def main():
            success={}         
            settings = Settings() 

            @defer.inlineCallbacks
            def getResponse(proxy,request):
                try:
                    print("Request {} using proxy:{}".format(request,proxy))
                    response = yield HTTP11DownloadHandler(settings).download_request(request=request,spider=None)
                    if response.status==200:
                        success[proxy]=success.setdefault(proxy,0) + 1
                        print("Successful(+{}/{}) ip:{}".format(success[proxy],self.checknum,proxy))
                        if success[proxy]/self.checknum>= self.checkthreshold:
                            self.passproxy.add(proxy)    
                except Exception as e:
                    #print(e)
                    pass

            def output_better_proxy(_):
                """ writing proxies to file"""
                with open('validProxy.txt','w') as f:
                    for p in self.passproxy:
                        print(p)
                        f.write(p+'\n')

            def iter_proxy():
                # work needs to be a generator, i tried to use list but failed to realize concurrent
                work = (    getResponse(proxy,Request(url='http://myip.dnsdynamic.org',
                                    headers=self.headers,
                                    meta={ 'proxy':"http://"+proxy, 'download_timeout':self.timeout})) for proxy in self.proxy_list for times in range(self.checknum)
                        )
                coop = task.Cooperator()
                join = defer.DeferredList(coop.coiterate(work) for i in range(self.concurrent))
                join.addCallback(output_better_proxy)
                join.addCallback(lambda _: reactor.stop())

            iter_proxy()

        main()
        reactor.run()

           
if __name__ == '__main__':
    """ crawl proxy without stop, but rest certain seconds after every time
    """
    findProxy = find_http_proxy(parse_args())
    #findProxy = find_http_proxy(country="China",reverse=True)
    print("starting...")
    start = time.time()
    findProxy.getherproxy_req()
    findProxy.proxy_checker()

    
    def saveproxy():
        with open("validProxy.txt",'w') as fd:
            for proxy in findProxy.passproxy:
                fd.write(proxy+"\n")
        print("length of successful proxy is %d" % len(findProxy.passproxy))
        print("finished writing to validProxy.txt")
        print("Entire job took: %s" % (time.time()-start))
        
    saveproxy()
