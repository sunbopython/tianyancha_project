#!/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from scrapy.dupefilters import RFPDupeFilter

class VerboseRFPDupeFilter(RFPDupeFilter):

    def log(self, request, spider):
        msg = "Filtered duplicate request: %(request)s"
        self.logger.debug(msg, {'request': request}, extra={'spider': spider})

        spider.crawler.stats.inc_value('dupefilter/filtered', spider=spider)