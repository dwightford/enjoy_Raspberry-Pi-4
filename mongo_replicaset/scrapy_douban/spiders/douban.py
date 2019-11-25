# -*- coding: utf-8 -*-
import scrapy

import json

from ..items import ScrapyDoubanItem

class DoubanSpider(scrapy.Spider):
    name = 'douban'
    allowed_domains = ['movie.douban.com']
    start_urls = ['http://movie.douban.com/']

    def parse(self, response):
        url_tpl = "https://movie.douban.com/j/search_subjects?type=movie&tag={tag}&sort=recommend&page_limit=20&page_start={page}"

        #设置获取电影的tag列表
        #从HTML源码上看，tags应该在classname = tag-list的div中，实际HTML源码中没有
        #tags = response.xpath('//div[@class="tag-list"]')
        #从HTTP交互中找到页面上的电影tag是用URL动态获取的，简单处理，手动设置几个
        #获取tags的HTTP URL为 https://movie.douban.com/j/search_tags?type=movie&source=
        tags = ['热门','经典','华语']

        for tag in tags:
            # 可以自行调整抓取的页数 页数 = max/20
            max = 40
            start = 0
            while start <= max:
                url = url_tpl.format(tag=tag, page=start)
                yield scrapy.Request(url, callback=self.parse_movielist)
                start += 20

    def parse_movielist(self, respones):
        #respones是json字符串
        resjson = respones.body.decode()
        movielist = json.loads(resjson)

        urls = []

        for movie in movielist.get("subjects"):
            urls.append(movie["url"].replace('\/','/'))

        print(urls)

        for url in urls:
            yield scrapy.Request(url, callback=self.parse_movie)

    def parse_movie(self, respones):
        content = respones.xpath('//div[@id="content"]')
        item = ScrapyDoubanItem()

        #获取影片名称和发布年份
        item['moviename'] = content.xpath('./h1/span[1]/text()').extract_first()
        if content.xpath('./h1/span[2]'):
            year = content.xpath('./h1/span[2]/text()').extract_first()
            item['year'] = year[1:-1]

        #获取影片详情
        subject = content.xpath('//div[@class="subject clearfix"]')
        info = subject.xpath('//div[@id="info"]').xpath('string(.)').extract_first()
        item['info'] = info

        #获取影片评星
        interest_sectl = content.xpath('//div[@id="interest_sectl"]')
        item["stars"] = interest_sectl.xpath('//strong[@class="ll rating_num"]/text()').extract_first()

        #获取影片简介
        related_info = content.xpath('//div[@class="related-info"]')
        item["synopsis"] = related_info.xpath('//div[@class="indent"]/span[1]/text()').extract_first().strip()

        yield item