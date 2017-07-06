#!/usr/bin/python3
# -*- coding: utf-8 -*-


import logging
import random
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware


class RotateUserAgentMiddleware(UserAgentMiddleware):
    """useragent middleware"""

    useragent_list = []
    useragentFile = 'tianyancha/utils/useragentlist.txt'

    def __init__(self,user_agent="Scrapy"):
        self.user_agent = user_agent
        self.readuseragentfile()

    def process_request(self,request,spider):
        ua = random.choice(self.useragent_list)
        if ua:            
            # logging.info("Current UserAgent: "+ua) 
            request.headers.setdefault('User-Agent',ua)

    def readuseragentfile(self):
        """Read to useragent_list from file"""
        with open(self.useragentFile) as f:
            for line in f:
                self.useragent_list.append(line.strip('\n'))
            return len(self.useragent_list)