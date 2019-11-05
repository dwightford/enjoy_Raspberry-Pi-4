<center>玩转Raspberry Pi 4之MySQL数据库操作</center>

Raspberry Pi 4终于到手了。折腾开始!  

今天我们结合Scrapy折腾MySQL数据库！

&emsp;&emsp;MySQL是最流行的关系型数据库管理系统之一，也是服务器系统的必备组件之一。在Raspberry pi 4的安装源上并没有MysQL，但有MariaDB。MariaDB数据库管理系统由MySQL的创始人麦克尔•维德纽斯主导开发，是MySQL的一个分支，主要由开源社区在维护，采用GPL授权许可。开发这个分支的原因之一是：甲骨文公司收购了MySQL后，有将MySQL闭源的潜在风险，因此社区采用分支的方式来避开这个风险。  
&emsp;&emsp;MariaDB的目的是完全兼容MySQL，包括API和命令行，使之能轻松成为MySQL的代替品。我们就在Raspberry pi 4上实践一下用爬虫爬取关系型数据，并存储到MariaDB。

1.系统配置
1.1 安装MariaDB
&emsp;&emsp;首先，我们来确认一下Raspberry pi 4的安装源上是否存在MySQL数据库。  

    pi@raspberrypi:~$ sudo apt-cache search mysql
    akonadi-backend-mysql - MySQL storage backend for Akonadi
    ampache - web-based audio file management system
    ......
    mariadb-server-10.0 - MariaDB database server binaries
    mariadb-server-10.3 - MariaDB database server binaries
    mariadb-server-core-10.0 - MariaDB database core server files
    mariadb-server-core-10.3 - MariaDB database core server files
    mariadb-test - MariaDB database regression test suite
    ......
    mysql-common - MySQL database common files, e.g. /etc/mysql/my.cnf
    mysql-sandbox - Install and set up one or more MySQL server instances easily
    mysql-utilities - collection of scripts for managing MySQL servers
    mysqltcl - interface to the MySQL database for the Tcl language
    ......
 
&emsp;&emsp;搜索出的安装包中没有MySQL服务的安装文件mysql-server。但存在MariaDB数据库服务的安装文件mariadb-server。
 
&emsp;&emsp;我们选择安装最新的版本10.3。  

    sudo apt-get install mariadb-server-10.3

&emsp;&emsp;安装完成后，确认一下MariaDB数据库是否正常。  

    pi@raspberrypi:~$ sudo mysql
    Welcome to the MariaDB monitor.  Commands end with ; or \g.
    Your MariaDB connection id is 13
    Server version: 10.3.17-MariaDB-0+deb10u1 Raspbian 10

    Copyright (c) 2000, 2018, Oracle, MariaDB Corporation Ab and others.

    Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

    MariaDB [(none)]> 
 
&emsp;&emsp;出现上面的提示表示已经连接到MariaDB数据库，数据库工作正常。

1.2 设置用户名密码  
&emsp;&emsp;默认情况下MariaDB安装好后没有配置访问用户的密码，如果需要远程连接时会无法连接，因此需要对root用户设置密码。用sudo mysql命令连接至MariaDB，进行密码的修改。  

	use mysql;
	UPDATE user SET password=password('123456') WHERE user='root';
	UPDATE user SET plugin='mysql_native_password' WHERE user = 'root'; 
	FLUSH PRIVILEGES;
	exit

&emsp;&emsp;修改完成后，重启数据库服务。  

	sudo systemctl restart mariadb

&emsp;&emsp;重新连接MariaDB数据库，已经需要密码登录。  

    pi@raspberrypi:~$ sudo mysql -u root -p
    Enter password: (输入设置的密码'123456')
    Welcome to the MariaDB monitor.  Commands end with ; or \g.
    ......

&emsp;&emsp;输入密码才能进入数据库命令行界面。  
&emsp;&emsp;这样MariaDB数据库安装并配置成功。

1.3 安装pymysql  
&emsp;&emsp;pymysql是在Python中用于连接 MySQL服务器的驱动库。我们在Python3环境中存储关系型数据时，需要用到这个库。  
&emsp;&emsp;在pymysql中提供了Connection和Cursor对象来管理操作MySQL。  
&emsp;&emsp;其中Connection对象用于和MySQL Server的socket连接，使用connect方法来创建一个连接实例。connect方法的参数包括数据库服务器IP地址、端口、用户名、密码、连接的数据库名称等。  
&emsp;&emsp;Cursor对象用于和MySQL数据库的交互，使用Connection.Cursor()在当前socket连接上的进行数据库操作，包括建数据库、建表、增删改查、事务操作等。  
&emsp;&emsp;在python3环境中的安装命令如下：  

    sudo pip3 install pymysql

2.编写scrapy爬虫  
&emsp;&emsp;企查查是一个查询国内各个省市的企业信息的网站。企业信息是标准的关系型数据。我们就以企查查网站www.qichacha.com为例，来实践MariaDB数据库的数据库创建、表的创建、表数据的存储。  
2.1 新建爬虫  
&emsp;&emsp;2.1.1创建工程  

    scrapy startproject scrapy_qichacha

&emsp;&emsp;2.1.2创建爬虫  

	scrapy genspider qichacha www.qichacha.com

&emsp;&emsp;2.1.3 去除setting.py中把ITEM-PIPELINES开关注释  
&emsp;&emsp;2.1.4 网站抓取数据太快的话，会出现服务器访问错误，因此我们设置0.5秒发送一个请求，在setting.py中修改DOWNLOAD-DELAY = 0.5  
2.2 封装mysqlobj类  
&emsp;&emsp;为了在爬虫代码中简化数据库访问的操作，封装mysqlobj类管理MariaDB数据库的连接和操作，包括数据库的创建、连接、执行SQL命令等。代码文件为utils/mysql.py。  
&emsp;&emsp;在连接MariaDB数据库时，要判断用于存储公司信息的company-infos数据库是否已经存在，如果不存在，自动创建company-infos数据库。  
2.3 分析网站  
&emsp;&emsp;打开企查查主页，在页面上的企业查询部分，可以看到有"按区域"和"按行业"两种查询方式。  
&emsp;&emsp;我们按照区域查询的方式来抓取数据。  
&emsp;&emsp;以"北京"为例，我们点击"北京"的链接，进入"北京"的页面，可以看到有北京的所属市区和市区内的公司信息。  
&emsp;&emsp;从网页信息上看，已经建立好了省份、市区和公司的所属关系，因此我们可以在数据库中创建省份表、市县表和公司表这3张表来存储对应的信息。  

2.4 抓取省份信息  
&emsp;&emsp;我们来分析一下主页的HTML代码，在classname为areacom的div中，存放了所有省份和直辖市的链接，我们可以从中抓取省份和对应的URL信息。

    <div class="areacom" style="overflow: hidden; width: auto; height: 400px;">
        <div class="pills pills-title">
            <div class="pills-item"> 
                <a onclick="zhugeTrack('主页按钮点击',{'按钮名称':'企业查询-按区域'});" href="/g_BJ"> 北京 </a>
            </div>
            <div class="pills-item">
                <a onclick="zhugeTrack('主页按钮点击',{'按钮名称':'企业查询-按区域'});" href="/g_SH"> 上海 </a>
            </div>
            ......
        </div>
        <div class="pills">
            <div class="pills-header">
                <a onclick="zhugeTrack('主页按钮点击',{'按钮名称':'企业查询-按区域'});" href="/g_AH"> 安徽 </a>
            </div>
            <div class="pills-after">
            ......
            </div>
        </div>
        <div class="pills">
            <div class="pills-header">
                <a onclick="zhugeTrack('主页按钮点击',{'按钮名称':'企业查询-按区域'});" href="/g_FJ"> 福建 </a>
            </div>
            <div class="pills-after">
            ......
            </div>
        </div>
        ......
    </div>
 
&emsp;&emsp;classname为pills-item的div中是4个直辖市的信息，classname为pills的div中是其它省份的信息。省份数据主要包括省份的名称和对应信息的URL。我们直接在爬虫的parser函数中获取HTML中对应的数据。  
&emsp;&emsp;我们建立ProvinceItem类来存放省份信息，并传递到pipeline.py中进行数据库存储。  

    class ProvinceItem(scrapy.Item):
        type = scrapy.Field()
        name = scrapy.Field()
        url  = scrapy.Field()
&emsp;&emsp;类中的type字段用于数据存储时判断数据的类型。1为省份数据，2为市县数据，3为公司数据。这样就可以在pipeline.py中判断数据类型并存储抓取的数据。  
&emsp;&emsp;省份信息相关的数据库命令有4条：  
&emsp;&emsp;1) sql-create-province-tbl： 用于创建省份表，省份表表名为tbl_province，有3个字段，自增型id、省份名称和省份信息的URL。

        sql_create_province_tbl = """CREATE TABLE company_infos.tbl_province  (
                                     id int(0) NOT NULL AUTO_INCREMENT,
                                     province_name varchar(32) NOT NULL,
                                     province_url varchar(128) NOT NULL,
                                     PRIMARY KEY (id)
                                  );"""
&emsp;&emsp;2) sql-check-tbl-province：用于检查省份表是否存在，避免重复创建  

        sql_check_tbl_province = """SELECT table_name FROM information_schema.TABLES WHERE table_name ='tbl_province';"""
&emsp;&emsp;3) sql-query-province：用于检查省份表中某个省是否已经存在，不存在再插入，避免重复。  

        sql_query_province = "SELECT * FROM tbl_province WHERE province_name='%s'"
&emsp;&emsp;4) sql-insert-province：用于给省份表插入新纪录  

        sql_insert_province = "INSERT INTO tbl_province (province_name, province_url) VALUES ('%s', '%s' )"
 
&emsp;&emsp;省份信息获取后，我们存储在provinces数组中，并循环获取数组中的URL，进行个省份的市县信息获取，并用parse_city(self, response)函数对市县信息进行处理。  
&emsp;&emsp;在访问省份信息的URL时，发现如果不带cookie时，会返回405错误，因此我们通过chrome浏览器的开发者工具，获取浏览器访问时的cookie，进行HTTP请求的伪装。
 
&emsp;&emsp;带上cookie的伪装请求python代码为：  

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
                      'zg_de1d1a35bfa24ce29bbf2c7eb17e6c4f':'%7B%22sid%22%3A%201571994308074%2C%22updated%22%3A%201571995626964%2C%22info%22%3A%201571987855242%2C%22superProperty%22%3A%20%22%7B%7D%22%2C%22platform%22%3A%20%22%7B%7D%22%2C%22utm%22%3A%20%22%7B%7D%22%2C%22referrerDomain%22%3A%20%22www.qichacha.com%22%2C%22zs%22%3A%200%2C%22sc%22%3A%200%7D',
                      'CNZZDATA1254842228':'363565439-1571115116-https%253A%252F%252Fwww.qichacha.com%252F%7C1572249122',
                      'hasShow': '1',
                      'acw_sc__v2' : '5db6ac114a22859e7ffec5c61dbb2a1a88e32ee4',
                      'Hm_lpvt_3456bee468c83cc63fb5147f119f1075':str(timestamp_now)
                  }
        yield scrapy.Request(url, cookies=cookies, callback=self.parse_city)

&emsp;&emsp;经过初步验证，cookie的Hm-lpvt-3456bee468c83cc63fb5147f119f1075字段为当前访问时的时间戳，每次访问时都需要设置，否则会出现数据错误；Hm-lvt-3456bee468c83cc63fb5147f119f1075字段为初次改页面的时间戳，如果爬取时出现数据错误，可以从chrome的访问数据中更新该字段的值。  
2.5 抓取市县信息  
&emsp;&emsp;进入省份页面，我们来分析一下页面的HTML代码。  

    <div class="col-md-12 no-padding-right">
	    <div class="panel b-a padder" style="margin-bottom: 15px;">
		    <div class="pills m-t">
			    <div class="pills-header">
					所属地区：
				</div>
				<div class="pills-after">
					<a class="pills-item " href="/g_AH.html">
						A - 安徽
					</a>
					<a class="pills-item active" href="/g_BJ.html">
						B - 北京
					</a>
					<a class="pills-item " href="/g_CQ.html">
						C - 重庆
					</a>
					......
					<a class="pills-item " href="/g_ZJ.html">
						Z - 浙江
					</a>
				</div>
			</div>
		</div>
		<div class="panel b-a padder" style="margin-bottom: 15px;">
			<div class="pills m-t">
				<div class="pills-header">
					所属市区：
				</div>
				<div class="pills-after">
					<a class="pills-item active" href="/g_BJ_110101.html">
						东城区
					</a>
					<a class="pills-item " href="/g_BJ_110102.html">
						西城区
					</a>
					......
					<a class="pills-item " href="/g_BJ_110119.html">
						延庆区
					</a>
				</div>
			</div>
		</div>
    </div>
   
&emsp;&emsp;页面中存在两个classname为"pills m-t"的div，第一个div存放了省份信息，可以获取到当前省份，第二个存放了当前省份的所属市县信息。市县数据包括市县名称、省份名称和市县信息对应的URL。我们在parser-city函数中用数组存储市县信息，并循环访问市县的URL去爬取各市县的公司信息，并建立parse-companypages(self, response)函数去处理爬取到的市县页面。  
&emsp;&emsp;我们建立CityItem类来存放省份信息，并传递到pipeline.py中进行数据库存储。  

    class CityItem(scrapy.Item):
        type = scrapy.Field()
        name = scrapy.Field()
        province = scrapy.Field()
        url = scrapy.Field()

&emsp;&emsp;这里，CityItem的type为2。  
&emsp;&emsp;市县信息相关的数据库命令有4条：  
&emsp;&emsp;1) sql-create-city-tbl： 用于创建市县表，省份表表名为tbl_city，有4个字段，自增型id、市县名称、省份名称和市县信息的URL。  

        sql_create_city_tbl = """CREATE TABLE company_infos.tbl_city  (
                               id int(0) NOT NULL AUTO_INCREMENT,
                               city_name varchar(32) NOT NULL,
                               province_name varchar(32) NOT NULL,
                               city_url varchar(128) NOT NULL,
                               PRIMARY KEY (id)
                              );"""

&emsp;&emsp;2) sql-check-tbl-city：用于检查市县表是否存在，避免重复创建  

        sql_check_tbl_city = """SELECT table_name FROM information_schema.TABLES WHERE table_name ='tbl_city';"""

&emsp;&emsp;3) sql-query-city：用于检查市县表中某个市县是否已经存在，不存在再插入，避免重复  

        sql_query_city = "SELECT * FROM tbl_city WHERE city_name='%s'"

&emsp;&emsp;4) sql-insert-city：用于给市县表插入新纪录  

        sql_insert_city = "INSERT INTO tbl_city (city_name, province_name, city_url) VALUES ('%s', '%s' ,'%s')"

2.6 抓取公司信息  
&emsp;&emsp;进入市县页面，我们看到每个市县的公司都很多，都有几百页。我们看一下这几百页公司信息的。

    <div class="text-left m-t-lg m-b-lg">
		<ul class="pagination pagination-md">
			<li class="current active">
				<span>
					1
				</span>
			</li>
			<li>
				<a class="num" href="/gongsi_area.html?prov=BJ&city=110101&p=2">
					2
				</a>
			</li>
            ......
			<li>
				<a class="num" href="/gongsi_area.html?prov=BJ&city=110101&p=11">
					11
				</a>
			</li>
            ......
			<li>
				<a class="end" href="/gongsi_area.html?prov=BJ&city=110101&p=500">
					500
				</a>
			</li>
		</ul>
    </div>
    
&emsp;&emsp;可以看到这几百页的URL中除了页码不同，其它部分都相同，因此，我们在parse-companypages函数中获取公司页面的URL信息和最后一页的页码，用数组生成这些页面的URL，进行循环访问，并建立parse_company(self, response)函数，处理页面中包含的公司信息。
    
    def parse_companypages(self, response):
        #获取每个城市公司信息的页数
        pagenum = int(response.xpath('//a[@class="end"]/text()').extract_first())
        #获取最后一个页面的URL信息，便于批量创建URL
        lastpage_href = response.xpath('//a[@class="end"]/@href').extract_first()
        href_pre = lastpage_href[ : lastpage_href.rindex('=')+1]

        company_page_urls = [self.start_urls[0] + href_pre[1:] + str(cnt) for cnt in range(1, pagenum + 1)]

        for url in company_page_urls:
            yield scrapy.Request(url, callback=self.parse_company)
    
&emsp;&emsp;继续分析页面中的公司信息，公司信息都在classname为m_srchList的table中，我们可以从table中获取该页面中包括的公司信息。  

    <table class="m_srchList">
		<tbody>
			<tr>
				......
				<td>
					<a href="/firm_46be382fd8ad25515c605ba1c3475e81.html" target="_blank"
				class="ma_h1">
					        北京百年兆邦收藏品有限公司
					</a>
					<div class="search-tags">
					</div>
					<p class="m-t-xs">
						法定代表人：
						<a class="text-primary" href="/pl_p2f8943d7c813a5a1f4a5b782d500e3c.html">
							贾海霞
						</a>
						<span class="m-l">
							注册资本：300万元人民币
						</span>
						<span class="m-l">
							成立日期：2007-03-15
						</span>
					</p>
					<p class="m-t-xs">
						邮箱：765987474@qq.com
						<span class="m-l">
							电话：13611120555
						</span>
						......
					</p>
					<p class="m-t-xs">
						地址：北京市东城区王家园胡同10号商之苑大厦627室(东二环)
					</p>
				</td>
				<td width="100" class="statustd">
					<span class="nstatus text-success-lt m-l-xs">
						在业
					</span>
				</td>
			</tr>
			<tr>
				......
			</tr>
			......
		</tbody>
	</table>
 
&emsp;&emsp;公司信息包括公司名称、法人、注册资金、成立日期、邮箱、电话、地址、状态、所属市县、所属省份。  
&emsp;&emsp;我们建立CompanyItem类来存放省份信息，并传递到pipeline.py中进行数据库存储。  

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

&emsp;&emsp;CompanyItem对象中的type=3。  
&emsp;&emsp;公司信息相关的数据库命令有4条：  
&emsp;&emsp;1) sql-create-company-tbl： 用于创建公司信息表，省份表表名为tbl_company，有12个字段，自增型id、公司名称、法人、注册资金、成立日期、邮箱、电话、地址、状态、所属市县、所属省份、公司详情的URL。  

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
&emsp;&emsp;2) sql-check-tbl-company：用于检查公司信息表是否存在，避免重复创建  

        sql_check_tbl_company = """SELECT table_name FROM information_schema.TABLES WHERE table_name ='tbl_company';"""

&emsp;&emsp;3) sql_query_company：用于检查公司信息表中某个公司是否已经存在，不存在再插入，避免重复

        sql_query_company = "SELECT * FROM tbl_company WHERE company_name='%s'"

&emsp;&emsp;4) sql_insert_company：用于给公司信息表插入新纪录  

        sql_insert_company = """INSERT INTO tbl_company
                                (company_name, company_owner, company_regcap, 
                                 company_date, company_email, company_tel, company_addr, 
                                 company_status,company_city, company_province, company_url)
                                 VALUES ('%s', '%s' ,'%s' ,'%s', '%s' ,'%s' ,'%s' ,'%s' ,'%s' ,'%s' ,'%s')"""

3.运行爬虫  
&emsp;&emsp;在命令行中，运行scrapy crawl qichacha, 爬虫就开始工作啦！
&emsp;&emsp;我们来看一下爬虫的成果。

        sudo mysql -u root -p 
&emsp;&emsp;进入MariaDB数据库操作界面。    
&emsp;&emsp;用"show databases;"命令查看数据库，company_infos数据库已经建立。

    	MariaDB [(none)]> show databases;
    	+--------------------+
    	| Database           |
		+--------------------+
		| company_infos      |
		| information_schema |
		| mysql              |
		| performance_schema |
		+--------------------+
		4 rows in set (0.008 sec)
     
&emsp;&emsp;进入company_infos数据库，用"show tables;"命令查看表，3个表都成功建立。

		MariaDB [(none)]> use company_infos;
		Reading table information for completion of table and column names
		You can turn off this feature to get a quicker startup with -A
	
		Database changed
		MariaDB [company_infos]> show tables;
		+-------------------------+
		| Tables_in_company_infos |
		+-------------------------+
		| tbl_city                |
		| tbl_company             |
		| tbl_province            |
		+-------------------------+
		3 rows in set (0.001 sec)

&emsp;&emsp;用select命令查看3个表的数据。  
&emsp;&emsp;1) 省份表tbl-province  

		MariaDB [company_infos]> select * from tbl_province;
		+----+---------------+--------------+
		| id | province_name | province_url |
		+----+---------------+--------------+
		|  1 | 北京          | /g_BJ        |
		|  2 | 上海          | /g_SH        |
		|  3 | 天津          | /g_TJ        |
		|  4 | 重庆          | /g_CQ        |
		|  5 | 安徽          | /g_AH        |
		|  6 | 福建          | /g_FJ        |
		......

&emsp;&emsp;2) 城市表tbl-city  

		MariaDB [company_infos]> select * from tbl_city;
		+-----+----------------------------------+---------------+---------------------+
		| id  | city_name                        | province_name | city_url            |
		+-----+----------------------------------+---------------+---------------------+
		|   1 | 广州市                            | 广东           | /g_GD_440100.html   |
		|   2 | 韶关市                            | 广东           | /g_GD_440200.html   |
		|   3 | 深圳市                            | 广东           | /g_GD_440300.html   |
		|   4 | 珠海市                            | 广东           | /g_GD_440400.html   |
		|   5 | 汕头市                            | 广东           | /g_GD_440500.html   |
		|   6 | 佛山市                            | 广东           | /g_GD_440600.html   |
		.......
 
&emsp;&emsp;2) 公司表tbl-company  

        MariaDB [company_infos]> select * from tbl_company;
		+-----+-------------------------------+---------------+----------------+--------------+-----------------------+-------------+-------------------------+----------------+--------------------------------+------------------+---------------------------------------------+
		| id  | company_name                  | company_owner | company_regcap | company_date | company_email         | company_tel | company_addr            | company_status | company_city                   | company_province | company_url                                 |
		+-----+-------------------------------+---------------+----------------+--------------+-----------------------+-------------+-------------------------+----------------+--------------------------------+------------------+---------------------------------------------+
		|   1 | 云浮市益丰农业有限公司            | 陈均乐         | 300            | 2019-07-18   |                       |             |                         | 在业           | 云浮市                           | 广东             | /firm_992f3440be4f019a73c691cc2b66ac43.html |
		|   2 | 云浮市三招石材有限公司            | 陈小勇         | 50             | 2017-12-05   |                       |             |                         | 在业           | 云浮市                           | 广东             | /firm_d1fc4c0e33e4ab83552d54498d652443.html |
		|   3 | 罗定市金鸡镇聚益水                | 罗林清        |                | 2019-08-15   |                       |             |                         | 在业           | 云浮市                           | 广东             | /firm_f647d8d6825e709ccd481dca32069b7d.html |
		|   4 | 郁南县都城镇精英校外托管服务中心    | 黎燕超        |                | 2019-08-15   |                       |             |                         | 在业           | 云浮市                           | 广东             | /firm_dac3330c9d7a36b253c1dfae912aba2e.html |
		|   5 | 云城区安捷五金经营部              | 黄月爱        |                | 2016-03-03   |                       |             |                         | 在业           | 云浮市                           | 广东             | /firm_4614b909d5139f755f8f601ef364b72e.html |
		|   6 | 郁南县罗沙玉桂沙糖桔专业合作社      | 陈英泉        | 8              | 2012-01-04   | 0797132@qq.com        | 435946439   | 940797132@qq.com        | 注销           | 云浮市                           | 广东             | /firm_f1fe932b6bb1e1a2fcb7d091506bf84e.html |
		......

 
&emsp;&emsp;数据都正常存储。  

&emsp;&emsp;MySQL数据库爬虫代码获取请访问：https://github.com/dangelzjj/enjoy_Raspberry-Pi-4


-
&emsp;&emsp;安微云是国内领先的基于Arm架构的云技术团队，提供虚拟化、数据分析、数据存储、文本处理、语义分析、自动化脚本等企业级云技术及服务。  
&emsp;&emsp;更多信息，请关注"安微云"公众号。