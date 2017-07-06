# -*- encoding: utf-8  -*-

"""
    DownloadHandler that use phantomjs to get webpage response

    For some wedsites, handle the javascript code involves a lot of work,however,if we can manipulate the
    web broswer, it would solve our problem.

    Phantomjs is such a good web broswer which use the same webkit like chorme.
    
"""

from __future__ import unicode_literals

from scrapy import signals
import logging
import time
from scrapy.signalmanager import SignalManager
from scrapy.responsetypes import responsetypes
from scrapy.xlib.pydispatch import dispatcher
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium import webdriver
from six.moves import queue
from twisted.internet import defer, threads
from twisted.python.failure import Failure
import datetime


class PhantomJSDownloadHandler(object):
    """ DownloadHandler that use phantomjs to get webpage response

    Attributes:
        settings: dict-like object
            Setting object from scrapy framework
        options: dict (defaults:PHANTOMJS_OPTIONS)
            Options of phantomjs like desired_capabilities
        run: int (default: 10)
            Number of concurrent phantomjs process
        queue: LIFO Queue
            Queue to store phantomjs drivers

    """

    def __init__(self, settings):
        self.settings = settings
        self.options = settings.get('PHANTOMJS_OPTIONS', {})\

        max_run = settings.get('PHANTOMJS_MAXRUN', 5)
        self.sem = defer.DeferredSemaphore(max_run)      # as a means of limiting parallelism
        self.queue = queue.LifoQueue(max_run)            # last in first out, the content is driver not request
        SignalManager(dispatcher.Any).connect(self._close, signal=signals.spider_closed)

    def download_request(self, request, spider):
        """use semaphore to guard a phantomjs pool"""
        return self.sem.run(self._wait_request, request, spider)

    def _wait_request(self, request, spider):
        request.meta["proxy"]="http://120.52.73.97:86"
        # initialize phantomjs driver using selenium's webdriver
        try:
            driver = self.queue.get_nowait()
        except queue.Empty:
            self.options = self._updating_phantomjs_option(self.options,request)
            driver = webdriver.PhantomJS(**self.options)

        # change proxy for phantomjs 
        if request.meta.get('proxy'):
            driver.command_executor._commands['executePhantomScript'] = ('POST', '/session/$sessionId/phantom/execute')
            driver.execute('executePhantomScript', {'script': '''phantom.setProxy('{}',{});'''.format(request.meta['proxy'][7:].split(":")[0],int(request.meta['proxy'][7:].split(":")[1])), 'args' : [] })
            logging.info("driver1 hash:{}, start time:{},proxy:{},url:{}".format(hash(driver),str(datetime.datetime.now()),request.meta['proxy'],request.url))
        
        def thread_get_page(): 
            """ 
            These days most of the web apps are using AJAX techniques. When a page is loaded to browser,the elements 
            within that page may load at different time intervals. This makes locating elements difficult, if the 
            element is not present in the DOM, it will raise ElementNotVisibleException exception. 

            Using waits, we can solve this issue. 

            There are two types of waits - implicit & explicit. An explicit wait makes WebDriver to wait for a certain condition
            to occur before proceeding further with executions. An implicit wait makes WebDriver to poll the DOM for a certain 
            amount of time when trying to locate an element.

            """
            conditional_waiting = 2
            print("driver hash:{}, start time:{},proxy:{},url:{}".format(hash(driver),str(datetime.datetime.now()),request.meta.get('proxy'),request.url))
            logging.info("driver2 hash:{}, start time:{},proxy:{},url:{}".format(hash(driver),str(datetime.datetime.now()),request.meta.get('proxy'),request.url))
            if conditional_waiting==1:
                # method 1: handle explicit waiting according to element
                try:
                    driver.get(request.url)
                    print("current_url1:{}".format(driver.current_url))
                    if request.meta.get('searchURL'):
                        company_ele = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'search_result_single')][1]/div[1]/div[1]/a[1]")))
                    else:
                        copyright = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, "nav-main-copyright")))
                except TimeoutException:
                    print('Timeout exception for url:{}'.format(request.url))
            elif conditional_waiting==2:
                # method 2: handle explicit waiting according to element
                #driver.implicitly_wait(30)
                driver.implicitly_wait(8)
                #driver.implicitly_wait(6)
                try:
                    driver.get(request.url)
                    if request.meta.get('searchURL'):
                        company_ele = driver.find_element_by_xpath("//div[contains(@class,'search_result_single')][1]/div[1]/div[1]/a[1]")
                    else:
                        copyright = driver.find_element_by_id("nav-main-copyright")
                except Exception as e:
                    logging.info('Exception:{} for url:{}'.format(e,request.url))

            elif conditional_waiting==3:
                # method 3: ghostdriver won't response when switch window until page is loaded
                driver.execute_script("window.open('{}'),'new_window')".format(request.url))
            driver.switch_to.window(driver.current_window_handle)
            

        dfd = threads.deferToThread(thread_get_page)
        dfd.addCallback(self._response, driver, spider)
        return dfd

    def _response(self, _, driver, spider):
        """ handle response of webpage

            Args:
                driver: phantomjs driver from selenium's webdriver

        """
        print("driver hash {},finish time:{},url:{}".format(hash(driver),str(datetime.datetime.now()),driver.current_url))
        body = driver.execute_script("return document.documentElement.innerHTML")  # comapre with outerHTML which has html tag
        if body.startswith("<head></head>"):  # cannot access response header in Selenium
            body = driver.execute_script("return document.documentElement.textContent")    # only text part, ignore tags
        url = driver.current_url
        respcls = responsetypes.from_args(url=url, body=body[:100])

        # according to different returning code,construct diffenent response object to other's component
        if  "403 Forbidden" in body or \
            "为确认本次访问为正常用户行为，请您协助验证" in body or \
            'You have attempted to use an application which is in violation of your internet usage policy' in body:
            from scrapy.shell import inspect_response
            inspect_response(response, self)
            resp = respcls(url=url,status=403,body=body, encoding="utf-8")
        elif  "<head></head><body></body>" in body or \
                    "<head><title>500 Internal Server Error</title></head>" in body or \
                    '<meta name="keywords" content="企业注册信息查询,企业工商信息查询,企业信用查询,企业信息查询">' in body or \
                    '<title>504 Gateway Time-out</title>' in body or \
                    '502 Bad Gateway' in body or \
                    'Maximum number of open connections reached.' in body or \
                    'Gateway Timeout' in body or \
                    'Sorry, the page you are looking for is currently unavailable' in body:
            resp = respcls(url=url,status=503,body=body, encoding="utf-8")
        else:
            resp = respcls(url=url,status=200, body=body, encoding="utf-8")
        
        #driver.save_screenshot("_response_"+url.split("?")[-1].split("/")[-1][:35]+'.png')

        response_failed = getattr(spider, "response_failed", None)
        if response_failed and callable(response_failed) and response_failed(resp, driver):
            driver.quit()
            return defer.fail(Failure())
        else:
            if datetime.datetime.now().minute%6==0:     # handle memory leak every 6 mins
                driver.quit()
            self.queue.put(driver)
            return defer.succeed(resp)

    def _updating_phantomjs_option(self,options,request=None):
        """ Updating some options of phantomjs."""
        if '--ignore-ssl-errors=true' not in options['service_args']:
            options['service_args'].append('--ignore-ssl-errors=true')
        if '--ssl-protocol=any' not in options['service_args']:
            options['service_args'].append('--ssl-protocol=any')
        if request:
            options['desired_capabilities']['phantomjs.page.settings.userAgent'] = request.headers['User-Agent'].decode()
        else:
            options['desired_capabilities']['phantomjs.page.settings.userAgent'] = self.settings.get('USER_AGENT')
        return options

    def _close(self):
        while not self.queue.empty():
            driver = self.queue.get_nowait()
            driver.close()