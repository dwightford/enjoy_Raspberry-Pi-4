# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo

from pymongo import ReadPreference

ReplicaSet = True

class ScrapyDoubanPipeline(object):
    def __init__(self):
        if ReplicaSet == False:
            host = '127.0.0.1'
            port = 27017
            dbname = 'douban'
            sheetname = 'movies'
            self.client = pymongo.MongoClient(host=host, port=port)
        else:
            dbname = 'movie_infos'
            sheetname = 'movies'
            self.client = pymongo.MongoClient(["192.168.1.3:27017", "192.168.1.8:27017"],
                                               replicaSet="movies", read_preference=ReadPreference.SECONDARY_PREFERRED)
            self.client.admin.authenticate("root", "root")

        db = self.client[dbname]
        self.moviedb = db[sheetname]

    def process_item(self, item, spider):
        data = dict(item)
        self.moviedb.insert(data)

    def close_spider(self, spider):
        self.client.close()

#Test
if __name__ == '__main__':
    client = pymongo.MongoClient(["192.168.1.3:27017", "192.168.1.8:27017"],
                                 replicaSet="movies", read_preference=ReadPreference.SECONDARY_PREFERRED)

    client.admin.authenticate("root", "root")

    dbname = 'douban'
    sheetname = 'movies'

    db = client[dbname]
    moviedb = db[sheetname]

    data = {"aa":"bb", "cc":"eee"}
    ret =  moviedb.insert(data)

    print(ret)
