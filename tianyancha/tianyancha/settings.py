# -*- coding: utf-8 -*-

# Scrapy settings for tianyancha project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'tianyancha'

SPIDER_MODULES = ['tianyancha.spiders']
NEWSPIDER_MODULE = 'tianyancha.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 \
           (KHTML, like Gecko) Chrome/33.0.1750.154 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# duplicate handles
#JOBDIR = "duplicate" 

# 
#DUPEFILTER_CLASS = 'tianyancha.dupefilters.VerboseRFPDupeFilter'

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 0
# The download delay setting will honor only one of:
CONCURRENT_REQUESTS_PER_DOMAIN = 16
CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True
#COOKIES_DEBUG = True


# Retry middleware setting
RETRY_ENABLED = True
# Retry many times since proxies often fail
RETRY_TIMES = 4  # initial response + 6 retries = 7 requests
#
RETRY_HTTP_CODES = [503]

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
   'Accept-Language': 'zh-CN,zh;q=0.8',
}

# USER DEFINED PHANTOMJS DOWNLOADER HANDLERS
DOWNLOAD_HANDLERS = {
  'http':'tianyancha.core.downloader.handlers.PhantomJSDownloadHandler',
  'https':'tianyancha.core.downloader.handlers.PhantomJSDownloadHandler',
}

# PHANTOMJS CONFIGURATION OPTIONS
PHANTOMJS_OPTIONS = {
  'desired_capabilities':{'phantomjs.page.settings.loadImages':False,
                          'javascriptEnabled':True,
                          'phantomjs.page.settings.localToRemoteUrlAccessEnabled':True},
  'service_args':['--disk-cache=true']
}

#limiting parallelism OF phantomjs processes numbers
PHANTOMJS_MAXRUN = 8

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'tianyancha.middlewares.MyCustomSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'tianyancha.downloadermiddlewares.rotate_useragent.RotateUserAgentMiddleware':400,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware':None,
    'tianyancha.downloadermiddlewares.retry.RetryMiddleware': 500,
    'tianyancha.downloadermiddlewares.rotateproxy.ProxyMiddleware': 750,
    #'tianyancha.downloadermiddlewares.rotateproxy.TopProxyMiddleware': 760,
}

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    
    'tianyancha.pipelines.TianyanchaPipeline': 300,
    #'tianyancha.pipelines.DuplicatesPipeline':350,
    'tianyancha.pipelines.TianyanchaPipelineJson':500,
    'tianyancha.pipelines.TianyanchaPipelineDB':600,
    
}

# Configure the feed item permutation,especially useful for csv export
FEED_EXPORT_FIELDS = ['keyword','name','used_name','url','phone','mail','website','last_update',
					'legalPersonName','reCapital','score','regStatus','regTime','industry',
					'regNum','companyType','orgCode','businessRange','regAuthority','passDate',
					'creaditCode','regAddress','seniorExecutive','investors','outInvestment','mainBranch',
					'lawSuit','mainBid','change','pattent','copyright']

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
