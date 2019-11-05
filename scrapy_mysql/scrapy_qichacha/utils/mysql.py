#!/usr/bin/env python

# -*- coding: utf-8 -*-

import pymysql

from subprocess import Popen,PIPE

host = "localhost"
port = 3306
mysql_db_name = "company_infos"
mysql_db_user = "root"
mysql_db_password = "123456"

sql_create_db = 'create database if not exists '+ mysql_db_name + ' default character set utf8 COLLATE utf8_general_ci'

class mysqlobj():
    def __init__(self,addr = 'localhost',port = 3306,usname = 'root',uspw = '123456',defDB = 'company_infos'):
        self.mysqladdr = addr #mysql地址
        self.mysqlport = port #mysql端口
        self.mysqlusername = usname #mysql登陆用户名
        self.mysqlpassword = uspw #mysql登陆密码
        self.mysqlDefaleDB = defDB #mysql默认登陆数据库
        self.connectManger = None #mysql连接管理器
        self.mysqlcursor = None #mysql消息收发器
        # 连接mysql数据库
        self._connectMysql()

    def _connectMysql(self):
        self.connectManger = pymysql.connect(
            host = self.mysqladdr,
            port = self.mysqlport,
            user = self.mysqlusername,
            passwd = self.mysqlpassword,
            charset = "utf8"
        )

        self.mysqlcursor = self.connectManger.cursor()

        self.checkdbs(self.mysqlDefaleDB)

    def checkdbs(self, dbname):
        self.mysqlcursor.execute('show databases;')
        rows = self.mysqlcursor.fetchall()

        for row in rows:
            for colume in row:
                if dbname in colume:
                    print('database ' + dbname + ' exist')
                    self.connectManger.select_db(dbname)
                    return

        print('database ' + dbname + ' not exist')
        command = sql_create_db
        self.mysqlcursor.execute(command)
        self.connectManger.select_db(dbname)

    def commit(self):
        self.connectManger.commit()

    def closeMysql(self):
        self.mysqlcursor.close()
        self.connectManger.close()

    #调用mysql命令
    def execute(self,cmdstr):
        if self.mysqlcursor:
            return self.mysqlcursor.execute(cmdstr)
        else:
            return -999  #mysql 未连接

    def inPutDataWithSqlFile(self,sqlfilepath):
        process = Popen('/usr/local/mysql/bin/mysql -h%s -P%s -u%s -p%s %s'%(self.mysqladdr, self.mysqlport, self.mysqlusername, self.mysqlpassword, self.mysqlDefaleDB), stdout=PIPE, stdin=PIPE, shell=True)
        output = process.communicate('source '+sqlfilepath)
        print(output)

if __name__ == '__main__':
    sqlobj = mysqlobj()

    sql_query_province = """SELECT * FROM tbl_province WHERE province_name='上海'"""
    ret = sqlobj.execute(sql_query_province)

    sqlobj.connectManger.commit()
    sqlobj.mysqlcursor.close()
    sqlobj.connectManger.close()

    print(ret)