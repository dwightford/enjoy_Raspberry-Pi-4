# -*- coding: utf-8 -*-
import scrapy
import time

from ..items import ProvinceItem,CityItem,CompanyItem

class QichachaSpider(scrapy.Spider):
    name = 'qichacha'
    allowed_domains = ['www.qichacha.com']
    start_urls = ['https://www.qichacha.com/']

    def __init__(self):
        pass

    def parse(self, response):
        provinces = []
        areapane = response.xpath('//div[@class="tab-pane fade"]')
        areacom = areapane.xpath('./div[@class="areacom"]')
        pillstitles = areacom.xpath('./div[@class="pills pills-title"]')
        for pills_item in pillstitles.xpath('./div[@class="pills-item"]'):
            province = ProvinceItem()
            province["name"] = pills_item.xpath('./a/text()').extract_first().strip()
            province["url"] = pills_item.xpath('./a/@href').extract_first()
            province["type"] = 1
            provinces.append(province)
            yield province

        pills = areacom.xpath('./div[@class="pills"]')
        for pills_item in pills:
            province = ProvinceItem()
            pillsheader = pills_item.xpath('./div[@class="pills-header"]')
            province["name"] = pillsheader.xpath('./a/text()').extract_first().strip()
            province["url"] = pillsheader.xpath('./a/@href').extract_first()
            province["type"] = 1
            provinces.append(province)
            yield province

        for item in provinces:
            url = self.start_urls[0] + item["url"][1:]+".html"
            timestamp_now = int(time.time())
            # 指定cookies,GET请求中不带cookie，会返回HTTP 405
            cookies = {
                'zg_did':'%7B%22did%22%3A%20%2216dce08afd0da-0b2c376276dc5d-38677b07-fa000-16dce08afd1898%22%7D',
                'UM_distinctid':'16dce08bb6fb71-0e66822bcad0e9-38677b07-fa000-16dce08bb708ab',
                'acw_tc':'65e21c1715719878555454988e582fde91a40b74d3b60b53ee4648c771',
                'QCCSESSID':'inhg14q9m4attcb2k6e02dldg3',
                'Hm_lvt_3456bee468c83cc63fb5147f119f1075':'1571994308',
                'zg_de1d1a35bfa24ce29bbf2c7eb17e6c4f':'%7B%22sid%22%3A%201571994308074%2C%22updated%22%3A%20157199562696' \
                                                      '4%2C%22info%22%3A%201571987855242%2C%22superProperty%22%3A%20%22%7B%7D' \
                                                      '%22%2C%22platform%22%3A%20%22%7B%7D%22%2C%22utm%22%3A%20%22%7B%7D%22%2C%22' \
                                                      'referrerDomain%22%3A%20%22www.qichacha.com%22%2C%22zs%22%3A%200%2C%22sc%22%3A%200%7D',
                'CNZZDATA1254842228':'363565439-1571115116-https%253A%252F%252Fwww.qichacha.com%252F%7C1572249122',
                'hasShow': '1',
                'acw_sc__v2' : '5db6ac114a22859e7ffec5c61dbb2a1a88e32ee4',
                'Hm_lpvt_3456bee468c83cc63fb5147f119f1075':str(timestamp_now)}
            yield scrapy.Request(url, cookies=cookies, callback=self.parse_city)

    def parse_city(self, response):
        pillsmts = response.xpath('//div[@class="pills m-t"]')

        province_name = pillsmts[0].xpath('./div[@class="pills-after"]/a[@class="pills-item active"]/text()').extract_first()
        city_a_s = pillsmts[1].xpath('./div[@class="pills-after"]/a')

        citys = []

        for city_a in city_a_s:
            city = CityItem()
            city["name"] = city_a.xpath('./text()').extract_first()
            city["province"] = province_name[4:]
            city["url"] = city_a.xpath('./@href').extract_first()
            city["type"] = 2
            citys.append(city)
            yield city

        for city in citys:
            url = self.start_urls[0] + city["url"][1:]
            yield scrapy.Request(url, callback=self.parse_companypages)

    def parse_companypages(self, response):
        #获取每个城市公司信息的页数
        pagenum = int(response.xpath('//a[@class="end"]/text()').extract_first())
        #获取最后一个页面的URL信息，便于批量创建URL
        lastpage_href = response.xpath('//a[@class="end"]/@href').extract_first()
        href_pre = lastpage_href[ : lastpage_href.rindex('=')+1]

        company_page_urls = [self.start_urls[0] + href_pre[1:] + str(cnt) for cnt in range(1, pagenum + 1)]

        for url in company_page_urls:
            yield scrapy.Request(url, callback=self.parse_company)

    def parse_company(self, response):
        pillsmts = response.xpath('//div[@class="pills m-t"]')

        # 获取公司所在的省市名称
        province_name = pillsmts[0].xpath(
            './div[@class="pills-after"]/a[@class="pills-item active"]/text()').extract_first()
        city_name = pillsmts[1].xpath(
            './div[@class="pills-after"]/a[@class="pills-item active"]/text()').extract_first()

        companytable = response.xpath('//table[@class="m_srchList"]')

        companylist = companytable.xpath('./tbody/tr')

        for item in companylist:
            company = CompanyItem()
            company['type'] = 3
            company['city'] = city_name
            company['province'] = province_name[4:].strip()
            company['name'] = item.xpath('./td[2]/a/text()').extract_first().strip()
            company['url'] = item.xpath('./td[2]/a/@href').extract_first().strip()
            company['owner'] = item.xpath('./td[2]/p[1]/a/text()').extract_first().strip()
            #获取注册资金
            cptxt = item.xpath('./td[2]/p[1]/span[1]/text()').extract_first().strip()
            begin = cptxt.find('：')
            end = cptxt.find('万')
            if end > 0:
                company['registeredcapital'] = cptxt[begin+1:end]
            else:
                company['registeredcapital'] = '0'
            #获取成立日期
            datetxt = item.xpath('./td[2]/p[1]/span[2]/text()').extract_first().strip()
            begin = datetxt.find('：')
            end = datetxt.find('-')
            if end > 0:
                company['date'] = datetxt[begin+1:]
            else:
                company['date'] = '0'
            #获取公司邮箱
            emailtxt = item.xpath('./td[2]/p[2]/text()').extract_first().strip()
            begin = cptxt.find('：')
            if len(emailtxt) > 8:
                company['email'] = emailtxt[begin + 1:]
            else:
                company['email'] = '0'
            #获取公司电话
            teltxt = item.xpath('./td[2]/p[2]/span/text()').extract_first().strip()
            begin = cptxt.find('：')
            if len(emailtxt) > 8:
                company['tel'] = teltxt[begin + 1:]
            else:
                company['tel'] = '0'
            #获取公司地址
            addrtxt = item.xpath('./td[2]/p[2]/text()').extract_first().strip()
            begin = addrtxt.find('：')
            if len(emailtxt) > 8:
                company['address'] = addrtxt[begin + 1:]
            else:
                company['address'] = '0'
            #获取公司状态
            company['status'] = item.xpath('./td[3]/span/text()').extract_first().strip()
            yield company