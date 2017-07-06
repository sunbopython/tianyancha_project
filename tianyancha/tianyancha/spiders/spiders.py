#-*- coding: UTF-8 -*-

from scrapy.spiders import Spider
from scrapy.http import Request
from urllib.parse import urlencode
from tianyancha.items import CompanyItem
from parsel import Selector
from tianyancha.dbconnect import connectionLocal,connections

cur, conn = connectionLocal()   # database connnection

class TianyanchaSpider(Spider):

	name = 'tianyancha'
	keywords=[]        # company name list

	def __init__(self, name=None, **kwargs):
		super().__init__(name=None, **kwargs)

		with open("company_bj.txt",encoding='utf-8',errors='ignore') as f:
			for line in f:
				self.keywords.append(line.strip("\n"))
	
	def start_requests(self):
		for keyword in self.keywords:
			request = Request(url="http://bj.tianyancha.com/search?" + urlencode({'key':keyword}),priority=0,callback=self.after_search)
			request.meta['keyword'] = keyword
			request.meta['searchURL'] = True
			yield request

	def after_search(self,response):
		""" Parse search page response"""
		keyword = response.meta['keyword']
		company_url = response.xpath("//div[contains(@class,'search_result_single')][1]/div[1]/div[1]/a[1]/@href").extract()
		
		if company_url:    # this keyword has corresponding results
			print(company_url[0])
			item = CompanyItem()
			item['keyword'] = keyword
			item['url'] = company_url[0]
			item['fuzzy_results'] = response.xpath("//div[contains(@class,'search_result_single')]/div[1]/div[1]/a[1]/@href").extract()
			request = Request(url=company_url[0],priority=1,callback=self.parse_company)
			request.meta['item'] = item
			return request
		else:         
			with open(keyword+'no_result.html','w',encoding='utf-8') as f:
				f.write(response.body.decode('utf-8'))
			print("No result for keyword:{}".format(response.meta['keyword']))


	def parse_company(self,response):
		""" Parse company page response"""
		item = response.meta['item']
		item['name'] = response.xpath("//div[@class='company_info_text']/p[1]/text()").extract()
		item['used_name'] = response.xpath("//div[@class='company_info_text']/p[1]/span/a/text()").extract() or response.xpath("//div[@class='company_info_text']/p[1]/span/text()").extract() 
		item['phone'] = response.xpath("//div[@class='company_info_text']/span[1]/text()").extract()
		item['mail'] = response.xpath("//div[@class='company_info_text']/span[2]/text()").extract()
		item['website'] = response.xpath("//div[@class='company_info_text']/span[3]/span/text()").extract()
		item['last_update'] = response.xpath("//span[@ng-if='company.updateTime']/text()").extract()
		item['legalPersonName'] = response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[1]/tbody/tr[2]/td[1]/p/a/text()").extract()
		item['reCapital'] = response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[1]/tbody/tr[2]/td[2]/p/text()").extract()
		item['score'] = response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[1]/tbody/tr[1]/td[3]/img/@ng-alt").extract()
		item['regStatus'] = response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[1]/tbody/tr[4]/td[1]/p/text()").extract()
		item['regTime'] = response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[1]/tbody/tr[4]/td[2]/p/text()").extract()
		item['industry'] = response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[2]/tbody/tr[1]/td[1]/div/span/text()").extract()
		item['regNum'] = response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[2]/tbody/tr[1]/td[2]/div/span/text()").extract()
		item['companyType'] = response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[2]/tbody/tr[2]/td[1]/div/span/text()").extract()
		item['orgCode'] = response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[2]/tbody/tr[2]/td[2]/div/span/text()").extract()
		item['businessRange']=response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[2]/tbody/tr[3]/td[1]/div/span/text()").extract()
		item['regAuthority']=response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[2]/tbody/tr[3]/td[2]/div/span/text()").extract()
		item['passDate']=response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[2]/tbody/tr[4]/td[1]/div/span/text()").extract()
		item['creaditCode']=response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[2]/tbody/tr[4]/td[2]/div/span/text()").extract()
		item['regAddress']= response.xpath("//div[@id='nav-main-baseInfo']/following-sibling::div[1]/table[2]/tbody/tr[5]/td[1]/div/span/text()").extract()

		t1 = response.xpath("//div[@id='nav-main-staff']/following-sibling::div[1]/table/tbody/tr[1]/td/a/text()").extract()
		t2 = response.xpath("//div[@id='nav-main-staff']/following-sibling::div[1]/table/tbody/tr[2]/td")
		item['seniorExecutive'] = [t1[index]+"-"+ i.re(r'[\u4e00-\u9fa5]+').__str__() for index,i in enumerate(t2)]
		item['investors'] = response.xpath("//div[@id='nav-main-investment']/following-sibling::div[1]/div/div[1]/div/a/text()").extract()
		item['outInvestment'] = response.xpath("//div[@id='nav-main-outInvestment']/following-sibling::div[1]/div/div[1]/div/a/span/text()").extract()
		item['mainBranch'] = response.xpath("//div[@id='nav-main-branch']/following-sibling::div[1]/div/p/a/text()").extract()
		item['lawSuit'] = response.xpath("//div[@id='nav-main-lawSuit']/following-sibling::div/div/a/text()").extract()
		item['mainBid'] = response.xpath("//div[@id='nav-main-bid']/div/div[1]/a/text()").extract()
		tp1 = response.xpath("//div[@id='nav-main-changeInfo']/following-sibling::div/div[2]/div[1]/text()").extract()
		tp2 = response.xpath("//div[@id='nav-main-bid']/div/div[1]/a/text()").extract()
		tp3 = response.xpath("//div[@id='nav-main-changeInfo']/following-sibling::div/div[1]/div[1]/span[2]").extract()
		item['changes'] = ["变更前："+i +"  "+ "变更后: " +j for i in tp1 for j in tp2]
		item['pattent'] = response.xpath("//div[@id='nav-main-patent']/div/div[1]/div[1]/span[2]/text()").extract()
		item['copyright'] = response.xpath("//div[@id='nav-main-copyright']/div/div[1]/div[1]/text()").extract()				

		return item