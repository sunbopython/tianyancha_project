# *- coding:utf-8 -*-

from scrapy.item import Item, Field


class CompanyItem(Item):
	# define the fields for your item here like:
	# name = scrapy.Field()

	url = Field()
	keyword = Field()
	fuzzy_results = Field()    		#  模糊匹配结果
	name = Field()  
	used_name =  Field()
	phone = Field()
	mail = Field()
	website = Field()
	last_update = Field()

	# 基本信息 id="nav-main-baseInfo"
	legalPersonName = Field()		# 法定代表人
	reCapital = Field()     		# 注册资本
	score = Field()                 # 评分
	regStatus = Field()				# 状态
	regTime = Field()				# 注册时间
	industry = Field()				# 行业
	regNum = Field()				# 工商注册号码
	companyType = Field()			# 企业类型
	orgCode = Field()				# 组织机构代码
	businessRange = Field()			# 营业期限
	regAuthority = Field()			# 登记机关
	passDate = Field()				# 核准日期
	creaditCode = Field()			# 统一信用代码
	regAddress = Field()			# 注册地址

	# 高管信息 id="nav-main-staff"
	seniorExecutive = Field()

	# 股东信息 id = "nav-main-investment"
	investors = Field()

	# 对外投资 nav-main-outInvestment
	outInvestment = Field()

	# 分支结构 nav-main-branch
	mainBranch = Field()

	# 法律诉讼 nav-main-lawSuit
	lawSuit = Field()

	# 招投标 nav-main-bid
	mainBid = Field()

	# 变更信息  nav-main-changeInfo
	changes = Field()

	# 专利 nav-main-patent
	pattent = Field()

	# 著作 nav-main-copyright
	copyright = Field()






