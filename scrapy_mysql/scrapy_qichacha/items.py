# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

"""
type:
   1: province
   2: city
   3: company
"""


class ProvinceItem(scrapy.Item):
    type = scrapy.Field()
    name = scrapy.Field()
    url = scrapy.Field()

class CityItem(scrapy.Item):
    type = scrapy.Field()
    name = scrapy.Field()
    province = scrapy.Field()
    url = scrapy.Field()

class CompanyItem(scrapy.Item):
    type = scrapy.Field()
    name = scrapy.Field()
    owner = scrapy.Field()
    registeredcapital = scrapy.Field()
    date = scrapy.Field()
    email = scrapy.Field()
    tel = scrapy.Field()
    address = scrapy.Field()
    status = scrapy.Field()
    city = scrapy.Field()
    province = scrapy.Field()
    url = scrapy.Field()
