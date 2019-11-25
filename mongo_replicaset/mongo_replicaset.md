<center>玩转Raspberry Pi 4之搭建MongoDB集群</center>

Raspberry Pi 4终于到手了。折腾开始!  

今天我们结合Scrapy折腾MongoDB集群！

&emsp;&emsp;MongoDB是一个跨平台的，面向文档的数据库，是当前NoSQL数据库产品中最热门的一种，是一种介于关系数据库和非关系数据库之间的产品。它支持的数据结构非常松散，类似json格式，可以存储比较复杂的数据类型。  
&emsp;&emsp;Mongodb的集群模式有三种：Master-Slaver模式、Replica Set模式、sharding模式，其中Replica set应用最为广泛。  
&emsp;&emsp;Replica Set是一组MongoDB实例组成的集群，由一个主（Primary）节点和多个备份（Secondary）节点构成。通过Replication，由Primary将更新的数据同步到其他实例上，这样每个MongoDB实例都有相同的数据集副本。当主节点崩溃，备份节点会自动将其中权重最高的成员升级为新的主节点；当集群为偶数台时，特别是一主一从架构时，还需要加入一个仲裁（Arbiter）节点，参与升级投票。Replica Set操作中一般读写数据都是在主（Primary）节点上，需要手动指定读库的备份（Secondary）节点，从而实现负载均衡。  
&emsp;&emsp;Replica Set通过维护冗余的数据库副本，能够实现数据的异地备份，读写分离和自动故障转移。  
&emsp;&emsp;下面我们就在Raspberry pi 4上搭建MongoDB一主一从架构的Replica Set集群，并结合前期完成的豆瓣电影爬虫来测试验证Replica Set集群。

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

&emsp;&emsp;由于只有一台Raspberry Pi 4，为了实践多台服务器的搭建，因此加入一台ubuntu 14.04的电脑作为备份（Secondary）节点搭建集群。为了保证MongoDB的一致，在ubuntu 14.04电脑上也安装MongoDB 2.4.14版本。在www.mongodb.org/dl/linux上找到linux/mongodb-linux-x86_64-2.4.14.tgz，下载安装。  

2.搭建ReplicaSet集群  
2.1 服务器分配  
&emsp;&emsp;一主一从架构的Replica Set集群中，需要有3个角色：一个主（Primary）节点、一个备份（Secondary）节点和一个仲裁（Arbiter）节点。  
&emsp;&emsp;我们在Raspberry Pi 4搭建主（Primary）节点和仲裁（Arbiter）节点，在ubuntu 14.04电脑上搭建备份（Secondary）节点。  
&emsp;&emsp;Raspberry Pi 4的IP地址是：192.168.1.3，ubuntu 14.04电脑的IP是：192.168.1.8。  

2.2 创建配置文件  
&emsp;&emsp;在/home/pi下创建配置目录mongo_repset，在目录中分别创建master和arbiter目录存放配置文件和数据。  

      pi@raspberrypi:~$ cd mongo_repset/
      pi@raspberrypi:~/mongo_repset$ ls
      arbiter  master
&emsp;&emsp;主（Primary）节点配置文件：  

      pi@raspberrypi:~/mongo_repset/master$ vim mongodb_master.conf 
      #master.conf
      dbpath=/home/pi/mongo_repset/master
      logpath=/home/pi/mongo_repset/master/master.log
      pidfilepath=/home/pi/mongo_repset/master/master.pid
      #keyFile=/home/pi/mongo_repset/mongodb.key
      directoryperdb=true
      logappend=true
      replSet=movies
      bind_ip=192.168.1.3
      port=27017
      #auth=true
      oplogSize=100
      fork=true
      noprealloc=true
      #maxConns=4000

&emsp;&emsp;仲裁（Arbiter）节点配置文件：  

	  pi@raspberrypi:~/mongo_repset/arbiter$ vim mongodb_arbiter.conf 
	  #arbiter.conf
	  dbpath=/home/pi/mongo_repset/arbiter
	  logpath=/home/pi/mongo_repset/arbiter/arbiter.log
	  pidfilepath=/home/pi/mongo_repset/arbiter/arbiter.pid
	  #keyFile=/home/pi/mongo_repset/mongodb.key
	  directoryperdb=true
	  logappend=true
	  replSet=movies
	  bind_ip=192.168.1.3
	  port=27019
	  #auth=true
	  oplogSize=100
	  fork=true
	  noprealloc=true
	  #maxConns=4000

&emsp;&emsp;在ubuntu 14.04电脑的/home/pp下创建配置目录mongo_repset，在目录中创建slave目录存放配置文件和数据。  

	  pp@pp-ThinkPad-S2-2nd-Gen:~/mongo_repset$ ls
	  slave
&emsp;&emsp;备份（Secondary）节点配置文件：  

      pp@pp-ThinkPad-S2-2nd-Gen:~/mongo_repset/slave$ vim 	mongodb_slave.conf 
	  #slave.conf
	  dbpath=/home/pp/mongo_repset/slave
	  logpath=/home/pp/mongo_repset/slave/slave.log
	  pidfilepath=/home/pp/mongo_repset/slave/slave.pid
	  #keyFile=/home/pp/mongo_repset/mongodb.key
	  directoryperdb=true
	  logappend=true
	  replSet=movies
	  bind_ip=192.168.1.8
	  port=27017
	  #auth=true
	  oplogSize=100
	  fork=true
	  noprealloc=true
	  #maxConns=4000

&emsp;&emsp;参数说明：  
&emsp;&emsp;dbpath：数据库数据存放目录  
&emsp;&emsp;logpath：数据库日志存放目录  
&emsp;&emsp;pidfilepath：数据库pid文件存放目录  
&emsp;&emsp;keyFile：节点之间用于验证文件，各个节点上的文件内容必须保持一致，文件权限都必须600，仅Replica Set模式有效  
&emsp;&emsp;directoryperdb：数据库是否分目录存放  
&emsp;&emsp;logappend：日志文件追加方式存放  
&emsp;&emsp;replSet：Replica Set的名字，我们定义为movies  
&emsp;&emsp;bind_ip：mongodb绑定的ip地址  
&emsp;&emsp;port：端口  
&emsp;&emsp;auth：是否开启验证  
&emsp;&emsp;oplogSize：设置oplog文件的大小（MB）  
&emsp;&emsp;fork：守护进程运行，创建进程  
&emsp;&emsp;moprealloc：是否禁用数据文件预分配  
&emsp;&emsp;maxConns：最大连接数，默认2000  

&emsp;&emsp;其中keyFile和auth选项要在集群配置好，添加验证用户后再启用。

2.3 启动MongoDB  
&emsp;&emsp;在Raspberry Pi 4和ubuntu 14.04电脑上分别启动MongoDB服务。  

	  pi@raspberrypi:~/mongo_repset$ mongod -f ./master/mongodb_master.conf
	  pi@raspberrypi:~/mongo_repset$ mongod -f ./arbiter/mongodb_arbiter.conf
	  pp@pp-ThinkPad-S2-2nd-Gen:~/mongo_repset$ mongod -f ./salve/mongodb_slave.conf
&emsp;&emsp;如果启动MongoDB服务出现错误，可以查看对应目录下的log文件，找到具体的错误原因。  

2.4 配置集群  
&emsp;&emsp;集群需要在主（Primary）节点上进行。  
&emsp;&emsp;连接主（Primary）节点的MongoDB：  

	  pi@raspberrypi:~/mongo_repset$ mongo 192.168.1.3:27017
	  MongoDB shell version: 2.4.14
	  connecting to: 192.168.1.3:27017/test
	  >

&emsp;&emsp;配置集群参数：  

	  > use admin
      switched to db admin
	  > cfg={ _id:"movies", members:[ {_id:0,host:'192.168.1.3:27017',priority:2}, {_id:1,host:'192.168.1.8:27017',priority:1}, {_id:2,host:'192.168.1.3:27019',arbiterOnly:true}] };
	  {
          "_id" : "movies",
          "members" : [
              {
                  "_id" : 0,
                  "host" : "192.168.1.3:27017",
                  "priority" : 2
              },
              {
                  "_id" : 1,
                  "host" : "192.168.1.8:27017",
                  "priority" : 1
              },
              {
                  "_id" : 2,
                  "host" : "192.168.1.3:27019",
                  "arbiterOnly" : true
              }
          ]
	  }
	  > rs.initiate(cfg)
	  {
          "info" : "Config now saved locally.  Should come online in about a minute.",
          "ok" : 1
	  }

&emsp;&emsp;备注：  
&emsp;&emsp;集群配置的cfg名字可自定义，只要跟mongodb参数不冲突，_id参数为Replica Set名字，members里面的优先级priority值高的为主（Primary）节点，对于仲裁（Arbiter）点一定要加上arbiterOnly:true，否则主备模式不生效。  
&emsp;&emsp;集群cfg配置生效：rs.initiate(cfg)  

&emsp;&emsp;集群配置生效后，我们查看一下集群状态：rs.status()  

	  movies:PRIMARY> rs.status()
	  {
          "set" : "movies",
          "date" : ISODate("2019-11-22T08:38:31Z"),
          "myState" : 1,
          "members" : [
              {
                  "_id" : 0,
                  "name" : "192.168.1.3:27017",
                  "health" : 1,
                  "state" : 1,
                  "stateStr" : "PRIMARY",
                  "uptime" : 758,
                  "optime" : Timestamp(1574411190, 1),
                  "optimeDate" : ISODate("2019-11-22T08:26:30Z"),
                  "self" : true
              },
              {
                  "_id" : 1,
                  "name" : "192.168.1.8:27017",
                  "health" : 1,
                  "state" : 2,
                  "stateStr" : "SECONDARY",
                  "uptime" : 718,
                  "optime" : Timestamp(1574411190, 1),
                  "optimeDate" : ISODate("2019-11-22T08:26:30Z"),
                  "lastHeartbeat" : ISODate("2019-11-22T08:38:30Z"),
                  "lastHeartbeatRecv" : ISODate("2019-11-22T08:38:30Z"),
                  "pingMs" : 15,
                  "syncingTo" : "192.168.1.3:27017"
              },
              {
                  "_id" : 2,
                  "name" : "192.168.1.3:27019",
                  "health" : 1,
                  "state" : 7,
                  "stateStr" : "ARBITER",
                  "uptime" : 718,
                  "lastHeartbeat" : ISODate("2019-11-22T08:38:29Z"),
                  "lastHeartbeatRecv" : ISODate("2019-11-22T08:38:29Z"),
                  "pingMs" : 0
              }
          ],
          "ok" : 1
	  }
&emsp;&emsp;可以看到，集群状态正常，其中"stateStr" : "PRIMARY"表示主（Primary）节点, "stateStr" : "SECONDARY"表示备份（Secondary）节点， "stateStr" : "ARBITER,表示仲裁（Arbiter）节点。  

2.5 集群验证  
&emsp;&emsp;集群搭建好了，接下来我们用停掉/重启主（Primary）节点的方法来看一下集群是否能正常切换主备节点。  
&emsp;&emsp;在Raspberry Pi 4上直接kill掉主（Primary）节点的mongod进程，然后连接ubuntu 14.04的备份（Secondary）节点，查询集群状态。  

	  movies:SECONDARY> rs.status()
	  {
          "set" : "movies",
          "date" : ISODate("2019-11-22T08:44:30Z"),
          "myState" : 1,
          "members" : [
              {
                  "_id" : 0,
                  "name" : "192.168.1.3:27017",
                  "health" : 0,
                  "state" : 8,
                  "stateStr" : "(not reachable/healthy)",
                  "uptime" : 0,
                  "optime" : Timestamp(1574411190, 1),
                  "optimeDate" : ISODate("2019-11-22T08:26:30Z"),
                  "lastHeartbeat" : ISODate("2019-11-22T08:44:28Z"),
                  "lastHeartbeatRecv" : ISODate("2019-11-22T08:44:23Z"),
                  "pingMs" : 0
              },
              {
                  "_id" : 1,
                  "name" : "192.168.1.8:27017",
                  "health" : 1,
                  "state" : 1,
                  "stateStr" : "PRIMARY",
                  "uptime" : 2310,
                  "optime" : Timestamp(1574411190, 1),
                  "optimeDate" : ISODate("2019-11-22T08:26:30Z"),
                  "electionTime" : Timestamp(1574412266, 1),
                  "electionDate" : ISODate("2019-11-22T08:44:26Z"),
                  "self" : true
              },
              {
                  "_id" : 2,
                  "name" : "192.168.1.3:27019",
                  "health" : 1,
                  "state" : 7,
                  "stateStr" : "ARBITER",
                  "uptime" : 1074,
                  "lastHeartbeat" : ISODate("2019-11-22T08:44:29Z"),
                  "lastHeartbeatRecv" : ISODate("2019-11-22T08:44:29Z"),
                  "pingMs" : 11
              }
          ],
          "ok" : 1
	  }
&emsp;&emsp;可以看到，集群中原先的主（Primary）节点状态变为"stateStr" : "(not reachable/healthy)", 原先的备份（Secondary）节点状态变为"stateStr" : "PRIMARY"，变为新的主（Primary）节点。  
&emsp;&emsp;重启Raspberry Pi 4上的主（Primary）节点后，再查询集群状态，又恢复成原先的状态。  
&emsp;&emsp;从上述验证中，可以看到集群的主备节点切换正常。  

2.6 配置keyfile  
&emsp;&emsp;为了保证集群之间的安全性，需要增加KeyFile安全认证机制，即在2.2章节中创建配置文件时，注释掉的keyFile配置项。  

&emsp;&emsp;使用keyfile认证，副本集中的每个mongod实例使用keyfile内容认证其他成员。只有有正确的keyfile的mongod实例可以加入副本集。keyfile的内容必须是6到1024个字符的长度，且副本集所有成员的keyfile内容必须相同。  

&emsp;&emsp;开启keyfile认证会默认开启auth认证，需要用户的auth认证才能连接MongoDB数据库，所以还需要创建用户。  

&emsp;&emsp;我们在集群中先创建用户，并在admin数据库进行认证。  

	  movies:PRIMARY> use admin
	  switched to db admin
	  movies:PRIMARY> db.addUser('root','root')
	  {
          "user" : "root",
          "readOnly" : false,
          "pwd" : "03cc80058e1ce2656837607a514ef9e0",
          "_id" : ObjectId("5ddb93859b94821e7360a96a")
	  }
	  movies:PRIMARY> db.auth("root","root")

&emsp;&emsp;用户创建好之后，关闭主备节点和arbiter节点的服务，可以直接kill掉进程。  
&emsp;&emsp;在Raspberry Pi 4上创建keyfile文件，并修改权限。  

      pi@raspberrypi:~/mongo_repset$ openssl rand -base64 128 > ./mongodb.key
      pi@raspberrypi:~/mongo_repset$ chmod 600 ./mongodb.key
&emsp;&emsp;创建完成后，把keyfile文件拷贝到ubuntu 14.04机器上。  
&emsp;&emsp;修改各个节点的配置文件，把原先注释掉的keyFile和auth配置项打开，并重启各个节点。重启服务时，有可能会遇到以下错误：    

	  invalid char in key file /home/pi/mongo_repset/mongodb.key: =
&emsp;&emsp;这是因为keyFile内容的结尾有'='字符，编辑keyFile文件直接删掉即可。这个错误跟MongoDB的版本有关。  

&emsp;&emsp;重新连接主（Primary）节点。  

	  pi@raspberrypi:~/mongo_repset$ mongo 192.168.1.3:27017/admin
	  MongoDB shell version: 2.4.14
	  connecting to: 192.168.1.3:27017/admin
	  > rs.status()
	  { "ok" : 0, "errmsg" : "unauthorized" }
&emsp;&emsp;如果不进行用户认证连接MongoDB，将无法查看集群状态。  

	  pi@raspberrypi:~/mongo_repset$ mongo 192.168.1.3:27017/admin -u root -p root
	  MongoDB shell version: 2.4.14
	  connecting to: 192.168.1.3:27017/admin
	  ......
	  movies:PRIMARY> rs.status()
	  {
          "set" : "movies",
          "date" : ISODate("2019-11-22T12:04:59Z"),
          "myState" : 1,
          "members" : [
              {
                  "_id" : 0,
                  "name" : "192.168.1.3:27017",
                  "health" : 1,
                  "state" : 1,
                  "stateStr" : "PRIMARY",
                  .......                    
&emsp;&emsp;用户认证连接MongoDB，可以正常参看集群状态。  

&emsp;&emsp;至此，MongoDB的副本集搭建完成。  

3.副本集验证  
&emsp;&emsp;我们结合豆瓣电影爬虫来验证副本集的数据同步。  
3.1 修改爬虫的MongoDB操作代码  
&emsp;&emsp;MongoDB的操作代码在pipelines.py中。爬取豆瓣电影数据后，把数据存储到movie-infos数据库中。 

      from pymongo import ReadPreference

	  ReplicaSet = True  #连接副本集: True

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
              self.client = pymongo.MongoClient(["192.168.1.3:27017", "192.168.1.8:27017"], replicaSet="movies", read_preference=ReadPreference.SECONDARY_PREFERRED)
              self.client.admin.authenticate("root", "root")

          db = self.client[dbname]
          self.moviedb = db[sheetname]
          .....

3.2 验证爬虫  
&emsp;&emsp;在命令行中，运行scrapy crawl douban, 爬虫就开始工作啦！  
&emsp;&emsp;我们来看一下爬虫的成果。  
 
&emsp;&emsp;连接集群主（Primary）节点，进入操作界面。    
&emsp;&emsp;用"show dbs"命令查看数据库，movie_infos数据库已经建立。  

	  movies:PRIMARY> show dbs;
	  admin   0.03125GB
	  local   0.15625GB
	  movie_infos     0.03125GB
 
&emsp;&emsp;进入movie_infos数据库，用"show collections"命令查看collections，collection  movies成功建立。  

	  movies:PRIMARY> use movie_infos
      switched to db movie_infos
      movies:PRIMARY> show collections;
      movies
      system.indexes

&emsp;&emsp;查看collection movies中的数据。  
      
      movies:PRIMARY> db.movies.find()
      { "_id" : ObjectId("5dd7e9b874fece69b4d1c70f"), "moviename" : "比悲伤更悲伤的故事 比悲傷更悲傷的故事", "year" : "2018", "info" : "\n        导演: 林孝谦\n        编剧: 吕安弦\n        主演: 陈意涵 / 刘以豪 / 张书豪 / 陈庭妮 / 吴映洁 / 禾浩辰 / 游大庆 / 石知田 / 黄丽玲 / 姚爱宁\n        类型: 爱情\n        \n        制片国家/地区: 中国台湾\n        语言: 汉语普通话\n        上映日期: 2018-11-30(中国台湾) / 2019-03-14(中国大陆)\n        片长: 105分钟\n        又名: More Than Blue\n        IMDb链接: tt9081562\n\n", "stars" : "4.8", "synopsis" : "唱片制作人张哲凯(刘以豪)和王牌作词人宋媛媛(陈意涵)相依为命，两人自幼身世坎坷只有彼此为伴，他们是亲人、是朋友，也彷佛是命中注定的另一半。父亲罹患遗传重症而被母亲抛弃的哲凯，深怕自己随时会发病不久人世，始终没有跨出友谊的界线对媛媛展露爱意。眼见哲凯的病情加重，他暗自决定用剩余的生命完成他们之间的终曲，再为媛媛找个可以托付一生的好男人。这时，事业有 成温柔体贴的医生(张书豪)适时的出现让他成为照顾媛媛的最佳人选，二人按部就班发展着关系。一切看似都在哲凯的计划下进行。然而，故事远比这里所写更要悲伤......" }
      { "_id" : ObjectId("5dd7e9b974fece69b4d1c710"), "moviename" : "一条狗的使命2 A Dog's Journey", "year" : "2019", "info" : "\n        导演: 盖尔·曼库索\n        编剧: W·布鲁斯·卡梅伦 / 玛雅·福布斯 / 凯瑟琳·迈克 / 华莱士·沃洛达斯基\n        主演: 丹尼斯·奎德 / 凯瑟琳·普雷斯科特 / 刘宪华 / 玛格·海根柏格 / 贝蒂·吉尔平 / 乔什·加德 / 艾比·莱德·弗特森 / 杰克·曼利 / 达妮埃拉·巴博萨 / 陈琦烨 / 杰夫·罗普 / 吉姆·科比\n        类型: 剧情 / 喜剧 / 家庭\n        \n        制片国家/地区: 中国大陆 / 印度 / 中国香港 / 美国\n        语言: 英语\n        上映日期: 2019-05-17(美国/中国大陆)\n        片长: 108分钟\n        又名: 再见亦是狗朋友2(港) / 狗狗的旅程(台) / 一条狗的旅程 / 为了与你相遇2 / A Dog's Purpose 2\n        IMDb链接: tt8385474\n\n", "stars" : "6.9", "synopsis" : "小狗贝利延续使命，在主人伊森的嘱托下，通过不断的生命轮回， 执着守护伊森的孙女CJ，将伊森对孙女的爱与陪伴，当做最重要的 使命和意义，最终帮助CJ收获幸福，再次回到主人伊森身边。" }
      { "_id" : ObjectId("5dd7e9ba74fece69b4d1c711"), "moviename" : "过春天", "year" : "2018", "info" : "\n        导演: 白雪\n        编剧: 白雪 / 林美如\n        主演: 黄尧 / 孙阳 / 汤加文 / 倪虹洁 / 江美仪 / 廖启智 / 焦刚\n        类型: 剧情\n        \n        制片国家/地区: 中国大陆\n        语言: 汉语普通话 / 粤语\n        上映日期: 2019-03-15(中国大陆) / 2018-09-08(多伦多电影节)\n        片长: 99分钟\n        又名: 分隔线 / 佩佩 / The Crossing\n        IMDb链接: tt8875366\n\n", "stars" : "7.7", "synopsis" : "单亲家庭出身的16岁女学生佩佩（黄尧 饰），她的城市既是香港、也是深圳，白天在香港上学，晚上回到深圳跟妈妈（倪虹洁 饰）住在一起，频繁地穿梭于两地。为了和闺蜜Joe（汤加文 饰）一起旅行的约定，为了自己的存在感，为了对Joe男友阿豪（孙阳 饰）懵懂的好感，她内心的冲动被点燃，“水客”成为了她的另一个身份，一段颇有“冒险”感的青春故事就此开始。" }
      ......

&emsp;&emsp;连接集群备份（Secondary）节点，进入操作界面。   
&emsp;&emsp;用"show dbs"命令查看数据库，movie_infos数据库已经建立。  

	  movies:SECONDARY> show databases;
	  admin   0.078125GB
	  local   0.203125GB
	  movie_infos     0.078125GB

&emsp;&emsp;进入movie_infos数据库，用"show collections"命令查看collections，会出现以下错误，这是因为eplica set 中的备份（Secondary）默认是不可读的，用rs.slaveOk()命令设置一下即可。  

	  movies:SECONDARY> show collections
	  Fri Nov 22 22:08:02.275 error: { "$err" : "not master and 	slaveOk=false", "code" : 13435 } at src/mongo/shell/query.js:128
	  movies:SECONDARY> rs.slaveOk();

&emsp;&emsp;重新查询，collection  movies成功建立。  

	  movies:SECONDARY> show collections
	  movies
	  system.indexes

&emsp;&emsp;查看collection movies中的数据，可以看到和主（Primary）节点中的数据一致。  
&emsp;&emsp;副本集工作正常。  

&emsp;&emsp;MongoDB数据库爬虫代码获取请访问：https://github.com/dangelzjj/enjoy_Raspberry-Pi-4

4.参考资料  
&emsp;&emsp;https://docs.mongodb.com/manual/  
&emsp;&emsp;https://docs.mongodb.com/manual/replication/  

-----
&emsp;&emsp;安微云是国内领先的基于Arm架构的云技术团队，提供虚拟化、数据分析、数据存储、文本处理、语义分析、自动化脚本等企业级云技术及服务。  
&emsp;&emsp;更多信息，请关注"安微云"公众号。