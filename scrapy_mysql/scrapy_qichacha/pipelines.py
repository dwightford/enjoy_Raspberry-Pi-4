# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from .utils.mysql import mysqlobj

sql_create_province_tbl = """CREATE TABLE company_infos.tbl_province  (
                             id int(0) NOT NULL AUTO_INCREMENT,
                             province_name varchar(32) NOT NULL,
                             province_url varchar(128) NOT NULL,
                             PRIMARY KEY (id)
                          );"""
sql_check_tbl_province = """SELECT table_name FROM information_schema.TABLES WHERE table_name ='tbl_province';"""
sql_query_province = "SELECT * FROM tbl_province WHERE province_name='%s'"
sql_insert_province = "INSERT INTO tbl_province (province_name, province_url) VALUES ('%s', '%s' )"

sql_create_city_tbl = """CREATE TABLE company_infos.tbl_city  (
                         id int(0) NOT NULL AUTO_INCREMENT,
                         city_name varchar(32) NOT NULL,
                         province_name varchar(32) NOT NULL,
                         city_url varchar(128) NOT NULL,
                         PRIMARY KEY (id)
                      );"""
sql_check_tbl_city = """SELECT table_name FROM information_schema.TABLES WHERE table_name ='tbl_city';"""
sql_query_city = "SELECT * FROM tbl_city WHERE city_name='%s'"
sql_insert_city = "INSERT INTO tbl_city (city_name, province_name, city_url) VALUES ('%s', '%s' ,'%s')"

sql_create_company_tbl = """CREATE TABLE company_infos.tbl_company  (
                             id int(0) NOT NULL AUTO_INCREMENT,
                             company_name varchar(255) NOT NULL,
                             company_owner varchar(64) NOT NULL,
                             company_regcap varchar(16) NULL,
                             company_date varchar(16) NULL,
                             company_email varchar(32) NULL,
                             company_tel varchar(32) NULL,
                             company_addr varchar(255) NULL,
                             company_status varchar(8) NULL,
                             company_city varchar(32) NOT NULL,
                             company_province varchar(32) NOT NULL,
                             company_url varchar(128) NOT NULL,
                             PRIMARY KEY (id)
                         );"""
sql_check_tbl_company = """SELECT table_name FROM information_schema.TABLES WHERE table_name ='tbl_company';"""
sql_query_company = "SELECT * FROM tbl_company WHERE company_name='%s'"
sql_insert_company = """INSERT INTO tbl_company
                        (company_name, company_owner, company_regcap, company_date, 
                         company_email, company_tel, company_addr, company_status,
                         company_city, company_province, company_url)
                         VALUES ('%s', '%s' ,'%s' ,'%s', '%s' ,'%s' ,'%s' ,'%s' ,'%s' ,'%s' ,'%s')"""

class ScrapyQichachaPipeline(object):
    def open_spider(self, spider):
        self.sqlobj = mysqlobj()

        # 如果tbl_province表是否存在，如果不存在，则创建tbl_province表
        ret = self.sqlobj.execute(sql_check_tbl_province)
        if (ret == 0):
            self.sqlobj.execute(sql_create_province_tbl)
            self.sqlobj.connectManger.commit()

        # 如果tbl_city表是否存在，如果不存在，则创建tbl_city表
        ret = self.sqlobj.execute(sql_check_tbl_city)
        if (ret == 0):
            self.sqlobj.execute(sql_create_city_tbl)
            self.sqlobj.connectManger.commit()

        # tbl_company，如果不存在，则创建tbl_city表
        ret = self.sqlobj.execute(sql_check_tbl_company)
        if (ret == 0):
            self.sqlobj.execute(sql_create_company_tbl)
            self.sqlobj.connectManger.commit()

    def process_item(self, item, spider):
        if item["type"] == 1:
            data = (item["name"], item["url"])

            #先确定province是否已经存在，避免重复插入
            ret = self.sqlobj.execute(sql_query_province % item["name"])
            if (ret == 0):
                self.sqlobj.execute(sql_insert_province % data)
                self.sqlobj.connectManger.commit()

            return item
        elif item["type"] == 2:
            data = (item["name"], item["province"], item["url"])

            # 先确定city是否已经存在，避免重复插入
            ret = self.sqlobj.execute(sql_query_city % item["name"])
            if (ret == 0):
                self.sqlobj.execute(sql_insert_city % data)
                self.sqlobj.connectManger.commit()

            return item
        elif item["type"] == 3:
            data = (item["name"], item["owner"],
                    (item["registeredcapital"] if item["registeredcapital"] != "0" else ""),
                    (item["date"] if item["date"] != "0" else ""),
                    (item["email"] if item["email"] != "0" else ""),
                    (item["tel"] if item["tel"] != "0" else ""),
                    (item["address"] if item["address"] != "0" else ""),
                    (item["status"] if item["status"] != "0" else ""),
                    item["city"],item["province"],item["url"]
                    )

            # 先确定company是否已经存在，避免重复插入
            ret = self.sqlobj.execute(sql_query_company % item["name"])
            if (ret == 0):
                self.sqlobj.execute(sql_insert_company % data)
                self.sqlobj.connectManger.commit()


    def close_spider(self, spider):
        self.sqlobj.mysqlcursor.close()
        self.sqlobj.connectManger.close()
