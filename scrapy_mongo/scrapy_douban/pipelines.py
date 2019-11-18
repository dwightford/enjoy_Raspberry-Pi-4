# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo

class ScrapyDoubanPipeline(object):
    def __init__(self):
        host = '127.0.0.1'
        port = 27017
        dbname = 'douban'
        sheetname = 'movies'
        self.client = pymongo.MongoClient(host=host, port=port)
        db = self.client[dbname]
        self.moviedb = db[sheetname]

    def process_item(self, item, spider):
        data = dict(item)
        self.moviedb.insert(data)

    def close_spider(self, spider):
        self.client.close()
