<center>玩转Raspberry Pi 4之MongoDB数据库操作</center>

Raspberry Pi 4终于到手了。折腾开始!  

今天我们结合Scrapy折腾MongoDB数据库！

&emsp;&emsp;MongoDB是一个跨平台的，面向文档的数据库，是当前NoSQL数据库产品中最热门的一种，是一种介于关系数据库和非关系数据库之间的产品。它支持的数据结构非常松散，类似json格式，可以存储比较复杂的数据类型。  
&emsp;&emsp;下面我们就在Raspberry pi 4上实践一下用爬虫爬取电影信息的数据，并存储到MongoDB。

1.系统配置  
1.1 安装MongoDB  

&emsp;&emsp;我们用apt-get命令安装。  

      sudo apt-get install mongodb

&emsp;&emsp;安装完成后，确认一下MongoDB服务是否正常。  

      pi@raspberrypi:~$ mongo
	  MongoDB shell version: 2.4.14
      connecting to: test
      Server has startup warnings: 
      Mon Nov 18 09:01:41.527 [initandlisten]
      ...... 
	  >  
 
&emsp;&emsp;出现上面的提示表示MongoDB数据库工作正常。  

1.2 配置服务目录  
&emsp;&emsp;我们为MongoDB配置一个自定义的目录，便于检查数据。    
&emsp;&emsp;先关闭已经启动的MongoDB服务。  

	  sudo killall mongod
&emsp;&emsp;在/home/pi目录下创建MongoDB的数据目录，并重启mongod服务。  

	  mkdir mongod_data
      mongod --dbpath /home/pi/mongod_data/ &
&emsp;&emsp;MongoDB数据库服务启动后，我们看一下mongod_data目录。  

	  pi@raspberrypi:~/mongo_data$ ls
	  local.0  local.ns  mongod.lock

&emsp;&emsp;看到数据库目录已经完成切换。  

1.3 安装pymongo  
&emsp;&emsp;pymongo是在Python中用于连接 MongoDB服务器的驱动库。我们在Python3环境中访问MongoDB数据库时，需要pymongo连接并操作数据库。  
&emsp;&emsp;由于Raspberry Pi 4上安装的MongoDB是2.4.14版本，在安装pymongo时，需要指定版本为3.2.0，否则会默认安装3.8.0版本，版本不兼容。  
&emsp;&emsp;在python3环境中的安装命令如下：  

      sudo pip3 install pymongo==3.2.0

2.编写scrapy爬虫  
&emsp;&emsp;豆瓣网是一个非常知名的社区网站。我们就以豆瓣电影网站movie.douban.com为例，结合scrapy爬虫抓取电影信息，来实践MongoDB数据库的数据库创建、collection的创建和document的存储。  
2.1 新建爬虫  
&emsp;&emsp;2.1.1创建工程  

    scrapy startproject scrapy_douban

&emsp;&emsp;2.1.2创建爬虫  

	scrapy genspider douban movie.douban.com

&emsp;&emsp;2.1.3 去除setting.py中把ITEM-PIPELINES开关注释  
&emsp;&emsp;2.1.4 网站抓取数据太快的话，会出现服务器访问错误，因此我们设置0.5秒发送一个请求，在setting.py中修改DOWNLOAD-DELAY = 0.5  

2.2 分析网站  
&emsp;&emsp;打开豆瓣电影主页，点击进入"选电影"页面，我们可以按照不同的标签来选电影，如"热门"、"最新"、"经典"等。  
&emsp;&emsp;我们以"热门"标签为例，来分析网页数据。选择"热门"标签后，具体电影的列表显示会以热度、时间、评价三种排序方式可供选择。  
&emsp;&emsp;我们选择默认的"按热度排序"方式，页面会显示20个电影信息，点击电影下方的"加载更多"后，会更新20个电影信息。  
&emsp;&emsp;点击具体电影后，会进入电影信息页面，我们可以在这个页面上抓取具体的影片信息，并存入MongoDB数据库。  
&emsp;&emsp;这样，整体的思路为：从"选电影"页面上抓取标签信息，然后轮询标签，抓取各个标签下的电影列表的URL，再从这些URL的页面上抓取具体的影片信息，存入MongDB数据库。  

2.3 抓取标签信息  
&emsp;&emsp;我们来分析一下豆瓣电影的HTML代码，在页面上显示标签的位置，并没有直接的标签信息，而是一个form表单。

      ......
      <div class="filter">
          <form action="get" class="gaia_frm" autocomplete="off">
              <input type="hidden" name="type" value="movie">
              <div class="tags">
                  <div class="tag-list"></div>
                  <div class="custom-frm" data-type="tag">
                      <input type="text" />
                      <button>确定</button>
                  </div>
              </div>
              ......
          </form>
          ......
      </div>
&emsp;&emsp;这样就必须是由JS启动获取具体的标签请求，来填充这个form。我们分析chrome浏览器的开发者工具中的"Network"交互数据，找到了获取具体标签的URL请求：  

      https://movie.douban.com/j/search_tags?type=movie&source=
&emsp;&emsp;我觉得这样做是有好处的，一方面可以动态更新网页上的标签信息，另一方面也可以根据登录用户的历史数据，展示用户更喜欢的影片信息。
 
&emsp;&emsp;我们简单处理标签问题，手动确定几个标签。  

      tags = ['热门','经典','华语']

2.4 抓取电影列表  
&emsp;&emsp;跟标签类似，电影的列表信息也是由另外的请求获取的。我们同样从"Network"交互数据中找到了请求的URL:  

	  https://movie.douban.com/j/search_subjects?type=movie&tag=%E7%83%AD%E9%97%A8&sort=recommend&page_limit=20&page_start=0
&emsp;&emsp;URL中有两个重要参数：tag为标签信息，page-start为获取影片的起始index，以步长20累加，每次点击"加载更多"，都会page-start都会增加20，取获取新的影片列表。  
&emsp;&emsp;我们定义parse-movielist函数来处理循环获取的电影列表：

      url_tpl = "https://movie.douban.com/j/search_subjects?type=movie&tag={tag}&sort=recommend&page_limit=20&page_start={page}"
      tags = ['热门','经典','华语']

      for tag in tags:
          # 可以自行调整抓取的页数 页数 = max/20
          max = 40
          start = 0
          while start <= max:
              url = url_tpl.format(tag=tag, page=start)
              yield scrapy.Request(url, callback=self.parse_movielist)
              start += 20

&emsp;&emsp;运行上述代码时，会出现以下错误：

	  2019-11-15 19:58:38 [scrapy.downloadermiddlewares.robotstxt] DEBUG: Forbidden by robots.txt: <GET https://movie.douban.com/j/search_subjects?type=movie&tag=%E7%83%AD%E9%97%A8&sort=recommend&page_limit=20&page_start=0>
      2019-11-15 19:58:39 [scrapy.core.engine] INFO: Closing spider (finished)

&emsp;&emsp;这是因为scrapy在爬取设定的URL之前，会先向服务器根目录请求一个robots.txt文件，这个文件规定了爬取范围，scrapy会查看自己是否符合权限，出错说明不符合，所以我们设定
不遵守这个协议。  
&emsp;&emsp;在settings.py中找到ROBOTSSTXT的设置项目，设为FALSE。

      ROBOTSTXT_OBEY = False

2.5 抓取影片信息  
&emsp;&emsp;请求返回的数据是标准的json数据，存放了20个影片的概要信息，我们可以从中获取影片详情的URL，并存放在数组中，然后循环获取影片详情。

      def parse_movielist(self, respones):
          #respones是json字符串
          resjson = respones.body.decode()
          movielist = json.loads(resjson)

          urls = []

          for movie in movielist.get("subjects"):
              urls.append(movie["url"].replace('\/','/'))

          for url in urls:
              yield scrapy.Request(url, callback=self.parse_movie)

&emsp;&emsp;返回的影片列表信息中包含16进制的UTF-8中文编码，需要先decode，才能转换成json结构。

2.7 存储影片信息  
&emsp;&emsp;进入影片详情页面，从页面的HTML代码中可以找到影片的详情都在id="content"的div中，直接解析获取即可。
&emsp;&emsp;我们在items.py中给影片信息定义5个字段，分别为：电影名字、详情、发布年份、评星、电影简介。  

	  class ScrapyDoubanItem(scrapy.Item):
	      moviename = scrapy.Field()
    	  info = scrapy.Field()
    	  year = scrapy.Field()
    	  stars = scrapy.Field()
          synopsis = scrapy.Field()
&emsp;&emsp;获取到影片详情后，存入MongoDB数据库。  
&emsp;&emsp;MongoDB中的数据库名字为douban，collection名字为movies。

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

3.运行爬虫  
&emsp;&emsp;在命令行中，运行scrapy crawl douban, 爬虫就开始工作啦！
&emsp;&emsp;我们来看一下爬虫的成果。
 
&emsp;&emsp;mongo命令，进入MongoDB数据库操作界面。    
&emsp;&emsp;用"show dbs"命令查看数据库，douban数据库已经建立。

	  pi@raspberrypi:~/scrapy_mongo$ mongo
	  MongoDB shell version: 2.4.14
	  ......
	  > show dbs
	  douban  0.0625GB
	  local   0.03125GB
&emsp;&emsp;进入douban数据库，用"show collections"命令查看collections，collection douban成功建立。

	  > use douban
	  switched to db douban
	  > show collections
	  movies
	  system.indexes

&emsp;&emsp;查看collection douban中的数据。  

	  > db.movies.find()
	  { "_id" : ObjectId("5dd3c5b374fece22577d3949"), "moviename" : "比悲伤更悲伤的故事 比悲傷更悲傷的故事", "year" : "2018", "info" : "\n        导演: 林孝谦\n        编剧: 吕安弦\n        主演: 陈意涵 / 刘以豪 / 张书豪 / 陈庭妮 / 吴映洁 / 禾浩辰 / 游大庆 / 石知田 / 黄丽玲 / 姚爱宁\n        类型: 爱情\n        \n        制片国家/地区: 中国台湾\n        语言: 汉语普通话\n        上映日期: 2018-11-30(中国台湾) / 2019-03-14(中国大陆)\n        片长: 105分钟\n        又名: More Than Blue\n        IMDb链接: tt9081562\n\n", "stars" : "4.8", "synopsis" : "唱片制作人张哲凯(刘以豪)和王牌作词人宋媛媛(陈意涵)相依为命，两人自幼身世坎坷只有彼此为伴，他们是亲人、是朋友，也彷佛是命中注定的另一半。父亲罹患遗传重症而被母亲抛弃的哲凯，深怕自己随时会发病不久人世，始终没有跨出友谊的界线对媛媛展露爱意。眼见哲凯的病情加重，他暗自决定用剩余的生命完成他们之间的终曲，再为媛媛找个可以托付一生的好男人。这时，事业有 成温柔体贴的医生(张书豪)适时的出现让他成为照顾媛媛的最佳人选，二人按部就班发展着关系。一切看似都在哲凯的计划下进行。然而，故事远比这里所写更要悲伤......" }
	  { "_id" : ObjectId("5dd3c5b574fece22577d394a"), "moviename" : "一条狗的使命2 A Dog's Journey", "year" : "2019", "info" : "\n        导演: 盖尔·曼库索\n        编剧: W·布鲁斯·卡梅伦 / 玛雅·福布斯 / 凯瑟琳·迈克 / 华莱士·沃洛达斯基\n        主演: 丹尼斯·奎德 / 凯瑟琳·普雷斯科特 / 刘宪华 / 玛格·海根柏格 / 贝蒂·吉尔平 / 乔什·加德 / 艾比·莱德·弗特森 / 杰克·曼利 / 达妮埃拉·巴博萨 / 陈琦烨 / 杰夫·罗普 / 吉姆·科比\n        类型: 剧情 / 喜剧 / 家庭\n        \n        制片国家/地区: 中国大陆 / 印度 / 中国香港 / 美国\n        语言: 英语\n        上映日期: 2019-05-17(美国/中国大陆)\n        片长: 108分钟\n        又名: 再见亦是狗朋友2(港) / 狗狗的旅程(台) / 一条狗的旅程 / 为了与你相遇2 / A Dog's Purpose 2\n        IMDb链接: tt8385474\n\n", "stars" : "6.9", "synopsis" : "小狗贝利延续使命，在主人伊森的嘱托下，通过不断的生命轮回， 执着守护伊森的孙女CJ，将伊森对孙女的爱与陪伴，当做最重要的 使命和意义，最终帮助CJ收获幸福，再次回到主人伊森身边。" }
	  ......

&emsp;&emsp;数据都正常存储。  

&emsp;&emsp;MongoDB数据库爬虫代码获取请访问：https://github.com/dangelzjj/enjoy_Raspberry-Pi-4


-
&emsp;&emsp;安微云是国内领先的基于Arm架构的云技术团队，提供虚拟化、数据分析、数据存储、文本处理、语义分析、自动化脚本等企业级云技术及服务。  
&emsp;&emsp;更多信息，请关注"安微云"公众号。