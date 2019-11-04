# -*- coding: utf-8 -*-
import scrapy
import time
import os

import requests

#DIR_PATH = os.path.abspath('..') + '/pic'

DIR_PATH = '/home/pi/usbdisk/pic'

class MzituSpider(scrapy.Spider):
    name = 'mzitu'
    allowed_domains = ['www.mzitu.com']
    begin = 4
    end = 5
    start_urls = ['https://www.mzitu.com/page/{cnt}'.format(cnt=cnt) for cnt in range(begin, end)]

    # 指定headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36',
        'refer': 'https://www.mzitu.com'
    }

    def parse(self, response):
        urls = []
        postlist = response.xpath('//div[@class="postlist"]')
        for li in postlist.xpath('./ul/li'):
            urls.append(li.xpath('./a/@href').extract_first())
        pic_urls = set(urls)
        for url in pic_urls:
            yield scrapy.Request(url, callback=self.parse_piclist, headers=self.headers)


    def parse_piclist(self, response):
        pagenavi = response.xpath('//div[@class="pagenavi"]')
        atags = pagenavi.xpath('./a')
        picnum = atags[-2].xpath('./span/text()').extract_first()
        last = atags[-2].xpath('./@href').extract_first().rindex('/')
        baseurl = atags[-2].xpath('./@href').extract_first()[:last]

        urls = [ baseurl + '/' + str(i) for i in range(0, (int(picnum) + 1)) ]
        for url in urls:
            yield scrapy.Request(url, callback=self.parse_pic, headers=self.headers)

    def parse_pic(self, response):
        picinfo = response.xpath('//div[@class="main-image"]/p/a/img')
        foldname = picinfo.xpath('./@alt').extract_first()
        picurl = picinfo.xpath('./@src').extract_first()
        download_refer = response.xpath('//div[@class="main-image"]/p/a/@href').extract_first()

        self.make_dir(foldname)
        picname = picurl[picurl.rindex('/')+1:]
        picpath = os.path.join(DIR_PATH, foldname, picname)

        if 'i5.' in picurl:
            newpicurl = picurl.replace('i5.', 'i6.', 2)
        else:
            newpicurl = picurl

        self.save_pic(newpicurl, picpath)

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, headers=self.headers, dont_filter=True)

    def make_dir(self, foldername):
        #新建文件夹并切换到该目录下
        path = os.path.join(DIR_PATH, foldername)
        if not os.path.exists(path):
            os.makedirs(path)
            print(path)
            os.chdir(path)
            return True
        print("Folder has existed!")
        return False

    def save_pic(self, picurl, picname):
        #保存图片到本地
        try:
            time.sleep(0.10)
            pic = requests.get(picurl, headers=self.headers, timeout=10)

            with open(picname, 'ab') as f:
                f.write(pic.content)
                print(picname)
        except Exception as e:
            print(e)
