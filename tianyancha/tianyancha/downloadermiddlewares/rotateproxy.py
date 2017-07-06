# coding: utf-8
"""
Author  jerryAn
Time    2016.05.04
"""

import random
import os
from queue import Queue
import logging
from datetime import datetime, timedelta
import time
from twisted.web._newclient import ResponseNeverReceived,ParseError
from twisted.internet.error import TimeoutError,ConnectionRefusedError, ConnectError,ConnectionLost,TCPTimedOutError
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.response import response_status_message


class Agent(object):
    """ Specify single proxy agent object

        Atttribute:
            proxy: like "http://45.78.34.180:8080"
            success: this proxy's life value (just like solder's blood value in game),\
                    it minus one if failed and plus one if successed
            percentage: proxy's percentage of successful useage, successful_times/total_using-times,default 100%
            absolute_threshold:
            percentage_threshold:
            label: valid or invalid
            last_condition: the success condition of last useage

    """
    def __init__(self,proxy, success=100, percentage=1, absolute_threshold=80, percentage_threshold=0.60):
        self.proxy = "http://" + str(proxy)  # for example: "http://45.78.34.180:8080"
        self.success = int(success) 
        self.percentage = percentage
        self.total = int(self.success/self.percentage)
        self.absolute_threshold = absolute_threshold
        self.percentage_threshold = percentage_threshold 
        self._set_label()
        self._set_last_condition()  

    def _set_label(self):
        """set label according to other argu
        """
        if self.success < self.absolute_threshold or \
                self.percentage < self.percentage_threshold:
            self.label = "invalid" 
        else:
            self.label = 'valid'

    def _set_last_condition(self,condition=True):
        """ Set last success use condition of the agent: True or False
        """
        self.last_condition = True if condition else False

    def weaken(self):
        """ After a failed usage
        """  
        self.total = self.total + 1
        self.success = self.success - 1
        self.percentage = self.success/self.total
        self._set_last_condition(condition=False)
        self._set_label()

    def stronger(self):         
        """ After a successful usage
        """       
        self.total = self.total + 1
        self.success = self.success + 1
        self.percentage = self.success/self.total
        self._set_last_condition(condition=True)
        self._set_label()

    def set_invalid(self):
        """direct way to change validation
        """
        self.last_condition = False
        self.label = "invalid"

    def is_valid(self):
        """bool"""
        return self.label == "valid"

    def __eq__(self,other):
        """"""
        return self.proxy == other.proxy

class ProxyMiddleware(object):
    """
        Customized Proxy Middleware

        No matter success or fail, change proxy for every request 
        

        Attributes:
            proxyfile: str, a txt file which consists of proxy
            proxyfileModificationTime: 
            agent_list: agent(proxy) list
            black_list: faild agent(proxy) list

    """
    # Change another proxy instead of passing to RetryMiddlewares when met these errors
    DONT_RETRY_ERRORS = (TimeoutError,ConnectionRefusedError,TCPTimedOutError,
                        ResponseNeverReceived, ConnectError)

    proxyfile = "tianyancha/utils/validProxy.txt"
    proxyfileModificationTime = None 
    blackfile = "tianyancha/utils/blacklist.txt"
    agent_list = []
    black_list = []   # store the failed agent proxies in a queue (size=300)
    used_agent = None

    def __init__(self):
        #self.readBlackfile()  # read black list file first
        self.readProxyfile()
        self.show_agent_condition()  # show initial agent condition 
        
    def readProxyfile(self):
        """get proxy from file"""       
        logging.info("Starting getting fresh proxies")
        with open(self.proxyfile) as f:
            for line in f:
                agent = Agent(line.strip('\n'))
                if agent not in self.agent_list and agent not in self.black_list:
                    self.agent_list.append(agent)
        self.proxyfilelastModificationTime = os.path.getmtime(self.proxyfile) 

#    def readBlackfile(self):
#        """ Store black list of proxy
#        """
#        with open(self.blackfile) as bk:
#            for line in bk:
#                agent = Agent(line.strip('\n'))
#                self.black_list.append(agent)

    def add_black_list_proxy(self,ag):
        """add black list proxy to its list, limits the size to 300 proxy"""
        if len(self.black_list)<300:
            self.black_list.append(ag)
        else:
            self.black_list.pop(0)  #delete the first proxy 
            self.black_list.append(ag)

    def writeBlackfile(self):
        """ Write invalid proxy to bk file,it has repeated data
        """
        with open(self.blackfile,'a') as bkf:
            for i in self.black_list:
                bkf.write(i.proxy[7:]+'\n')

    def update_agent_list(self):
        """ Remove invalid proxy from agent_list and add more proxy into this list
            Only when proxy file has been changed, been updated the agent_list
        """
        if os.path.getmtime(self.proxyfile) != self.proxyfilelastModificationTime:                   
            self.show_agent_condition()       # show current agent condition 

            logging.info("Agent pool need to be updated!!")
            # remove invalid proxy labeled by "invalid" 
            for ag in self.agent_list:
                if ag.is_invalid():
                    logging.info("This proxy {} (success {}) need to be eliminate, \
                                withdraw parameter percentage:{}".format(ag.proxy,ag.success,ag.percentage))
                    self.add_black_list_proxy(ag)
                    self.agent_list.remove(ag)

            # add more proxy into the pool  
            self.readProxyfile()
            self.writeBlackfile()
            
    def show_agent_condition(self):
        """ show condition of current agent
        """
        logging.info('[*******] %d current unique proxy remaining' % len(self.agent_list))
        logging.info('      Proxy              | Success  |     Total.Request      | Percentage      | label')
        for _ag in self.agent_list:
            ag_str = "{}        {}              {}                {:.2%}       {}".format(str(_ag.proxy),str(_ag.success),str(_ag.total),_ag.percentage,_ag.label)
            logging.info(ag_str)

    def _modifyAgentList(self,agent):
        # print(agent.proxy)
        try:
            originalagent = [i for i in self.agent_list if i.proxy==agent.proxy][0]
            self.agent_list[self.agent_list.index(originalagent)] = agent
        except IndexError:
            pass

    def _new_request_handle(self,request,reasontype):
        """ """
        new_request = request.copy()   # this request may has proxy meta data within it
        # new_used_agent = random.choice(list(filter(lambda x: x.is_valid(),self.agent_list)))
        # new_request.meta['agent'] = new_used_agent  # this is another agent object
        # new_request.meta['proxy'] = new_used_agent.proxy
        new_request.dont_filter = True
        if reasontype == 'status':
            logging.info("Changing <status problem> from failed proxy:{} to new one for processing {}".format(request.meta['proxy'],request.url))
        elif reasontype == 'exception':
            logging.info("Changing <exception problem> from failed proxy:{} to new one for processing {}".format(request.meta['proxy'],request.url))
        return new_request

    def process_request(self, request, spider):
        """"""
        self._process_request_with_proxy(request)


    def _process_request_with_proxy(self,request):
        """ Make request with proxy
        """
        valid_agent_number_in_agentlist = len(list(filter(lambda x: x.is_valid(),self.agent_list)))
        if valid_agent_number_in_agentlist < 100:
            self.update_agent_list()
        # following one line is replaced contemporyly for single proxy pressure test
        # used_agent = Agent("113.232.49.30:9529")
        # self.used_agent = Agent("120.52.73.96:8080")   # this proxy is alive now

        if not self.used_agent:   # especially for initialization  
            self.used_agent =  random.choice(list(filter(lambda x: x.is_valid(),self.agent_list)))
        else:
            if not self.used_agent.last_condition:  # if last use failed, switch to another proxy
                while not list(filter(lambda x: x.is_valid(),self.agent_list)).__len__():
                    logging.info("Proxy list has been used up! here comes long long waiting!!!")
                    time.sleep(30)    # in case the proxy has been used up!
                    self.update_agent_list()
                self.used_agent = random.choice(list(filter(lambda x: x.is_valid(),self.agent_list)))

        request.meta['agent'] = self.used_agent  # this is an agent object
        request.meta['proxy'] = self.used_agent.proxy

        logging.info("Request %(request)s using proxy:%(proxy)s",
                        {'request':request, 'proxy':request.meta['proxy']})
        return request

    def process_response(self, request, response, spider):
        """ Check response status and other validation info to decide whether to change a proxy or not
        """
        agent = request.meta.get('agent')
        reason = response_status_message(response.status)
        if response.status == 200:
            if "天眼查".encode() in response.body:
                print("Good proxy-Response pass through proxy middleware:{} for processing {}".format(request.meta['proxy'],response))
                logging.info("Good proxy:{} for processing {}".format(request.meta['proxy'],response))
                agent.stronger()
                return response
            else:
                print("Proxy {} meet faked {} ".format(agent.proxy,response.status))
                logging.info("Proxy {} meet faked {}".format(agent.proxy,response.status))
                agent.weaken()
                return self._new_request_from_response(request)
        elif response.status == 403:    # tianyancha 403 page doesn't have their logo string
            if not "You are not allowed to access this file".encode() in response.body:
                agent.set_invalid()
                print(agent.label)
                print("Proxy: {} meet {} for page:{} ".format(agent.proxy,reason,request.url))
                logging.info("Proxy: {} meet {} ".format(agent.proxy,reason))
                return self._new_request_from_response(request)
            else:
                print("Proxy: {} meet faked {} for page:{} ".format(agent.proxy,reason,request.url))
                logging.info("Proxy: {} meet faked {} ".format(agent.proxy,reason))
                return response
        elif response.status == 503:
            agent.weaken()

        return response


class TopProxyMiddleware(ProxyMiddleware):
    """
        Make statistics for the proxies during certain period, 
        then randomly choose one from the top 10(default) valid proxies to use

    """
    topindex = 10

    def process_request(self, request, spider):
        """ Make request random choose one in top ten proxies
        """
        self.maintaining_agent()
        tenthLargestPencentageValue = sorted(self.agent_list,key = lambda i: i.percentage)[-self.topindex].percentage 
        request.meta['agent'] = random.choice(list(filter(lambda x: x.is_valid() and x.percentage>=tenthLargestPencentageValue,self.agent_list)))
        request.meta['proxy'] = request.meta['agent'].proxy

        logging.info("Request %(request)s using proxy:%(proxy)s",
                        {'request':request, 'proxy':request.meta['proxy']})