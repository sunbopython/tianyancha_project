# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


from scrapy.exceptions import DropItem

class DuplicatesPipeline(object):
	""" Pipeline to get rid of repeated item"""

	def __init__(self):
		self.urls_seen = set()

	def process_item(self, item, spider):
		if item['url'] in self.urls_seen:
			print("Duplicate item found: %s" % item['url'])
			raise DropItem("Duplicate item found: %s" % item)
		else:
			self.urls_seen.add(item['url'])
			return item


class TianyanchaPipeline(object):
	""" Pipeline to eliminate useless HTML tags or useless strings
	"""

	def process_item(self, item, spider):
		for key, value in item.items():
			# handle list and useless HTML tag
			if(isinstance(value,list)):
				if value:   # eliminate empty list
					templist = []
					for obj in value:
						temp = '' if obj.strip()=='\n' or '' else obj.strip()
						templist.append(temp)
						#templist = [i.strip() for i in templist if i] # get rid of empty list element
					while '' in templist:
						templist.remove('')
					item[key] = ",".join(templist)
				else:
					item[key] = ""
		return item


class TianyanchaPipelineJson(object):
	""" Pipeline to output to json file
	"""

	def __init__(self):
		import codecs
		self.file = codecs.open("item.json", "wb", encoding="utf-8")

	def process_item(self, item, spider):
		import json
		line = json.dumps(dict(item), ensure_ascii=False) + "\n"
		self.file.write(line)
		return item

	def spider_closed(self, spider):
		self.file.close()


from tianyancha.dbconnect import connectionLocal,connections
conn = None

class TianyanchaPipelineDB(object):
	"""Pipeline to output to mysql database"""

	def __init__(self):
		self.setupDBCon()
		self.createTable()

	def process_item(self, item, spider):
		self.storeInDb(item)
		return item 

	def setupDBCon(self):
		self.cur, self.conn = connectionLocal()
		self.conn.set_charset('utf8')
		self.cur.execute('SET NAMES utf8;')
		self.cur.execute('SET CHARACTER SET utf8;')
		self.cur.execute('SET character_set_connection=utf8;')

	def createTable(self):
		"""Create table """
		#self.cur.execute("DROP TABLE IF EXISTS tianyancha_company")
		self.cur.execute("""CREATE TABLE IF NOT EXISTS tianyancha_company(id INT NOT NULL AUTO_INCREMENT,\
			keyword VARCHAR(255) default NULL COMMENT '搜索关键字',\
			fuzzy_results VARCHAR(1024) default NULL COMMENT '模糊匹配url',\
			name VARCHAR(255) default NULL COMMENT '公司名',\
			used_name VARCHAR(255) default NULL COMMENT '曾用名',\
			url VARCHAR(255) default NULL COMMENT '天眼查网址',\
			phone VARCHAR(255) default NULL COMMENT '电话',\
			mail VARCHAR(255) default NULL COMMENT '邮箱',\
			website VARCHAR(255) default NULL COMMENT '网址',\
			last_update VARCHAR(255) default NULL COMMENT '最近更新',\
			legalPersonName VARCHAR(255) default NULL COMMENT '法人代表',\
			reCapital VARCHAR(255) default NULL COMMENT '注册资本',\
			score VARCHAR(255) default NULL COMMENT '评分',\
			regStatus VARCHAR(255) default NULL COMMENT '状态',\
			regTime VARCHAR(255) default NULL COMMENT '注册时间',\
			industry VARCHAR(255) default NULL COMMENT '行业',\
			regNum  VARCHAR(255) default NULL COMMENT '工商注册号码',\
			companyType VARCHAR(255) default NULL COMMENT '企业类型',\
			orgCode VARCHAR(255) default NULL COMMENT '组织机构代码',\
			businessRange VARCHAR(255) default NULL COMMENT '营业期限',\
			regAuthority VARCHAR(255) default NULL COMMENT '登记机关',\
			passDate VARCHAR(255) default NULL COMMENT '核准日期',\
			creaditCode VARCHAR(255) default NULL COMMENT '统一信用代码',\
			regAddress VARCHAR(255) default NULL COMMENT '注册地址',\
			seniorExecutive TEXT default NULL COMMENT '高管信息',\
			investors TEXT default NULL COMMENT '股东信息',\
			outInvestment  TEXT default NULL COMMENT '对外投资',\
			mainBranch VARCHAR(255) default NULL COMMENT '分支机构',\
			lawSuit TEXT default NULL COMMENT '法律诉讼',\
			mainBid TEXT default NULL COMMENT '招投标',\
			changes TEXT default NULL COMMENT '变更信息',\
			pattent TEXT default NULL COMMENT '专利',\
			copyright TEXT default NULL COMMENT '著作',\
			PRIMARY KEY (id)\
			)""")


	def storeInDb(self,item):
		self.cur.execute("""INSERT INTO `tianyancha_company`(\
			`keyword`, \
			`fuzzy_results`, \
			`name`, \
			`used_name`, \
			`url`, \
			`phone`, \
			`mail`, \
			`website`, \
			`last_update`, \
			`legalPersonName`, \
			`reCapital`, \
			`score`, \
			`regStatus`, \
			`regTime`, \
			`industry`, \
			`regNum`, \
			`companyType`, \
			`orgCode`,\
			`businessRange`,\
			`regAuthority`,\
			`passDate`,\
			`creaditCode`,\
			`regAddress`,\
			`seniorExecutive`,\
			`investors`,\
			`outInvestment`,\
			`mainBranch`,\
			`lawSuit`,\
			`mainBid`,\
			`changes`,\
			`pattent`,\
			`copyright`\
			) \
			VALUE (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,\
					%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,\
					 %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",\
				(
				item.get('keyword'),
				item.get('fuzzy_results'),
				item.get('name'),
				item.get('used_name'),
				item.get('url'),
				item.get('phone'),
				item.get('mail'),
				item.get('website'),
				item.get('last_update'),
				item.get('legalPersonName'),
				item.get('reCapital'),
				item.get('score'),
				item.get('regStatus'),
				item.get('regTime'),
				item.get('industry'),
				item.get('regNum'),
				item.get('companyType'),
				item.get('orgCode'),
				item.get('businessRange'),
				item.get('regAuthority'),
				item.get('passDate'),
				item.get('creaditCode'),
				item.get('regAddress'),
				item.get('seniorExecutive'),
				item.get('investors'),
				item.get('outInvestment'),
				item.get('mainBranch'),
				item.get('lawSuit'),
				item.get('mainBid'),
				item.get('changes'),
				item.get('pattent'),
				item.get('copyright'),
				 ))


		self.conn.commit()

	def __del__(self):
		self.closeDB()

	def closeDB(self):
		self.conn.close()