<center>Play with Raspberry Pi 4 to build a MongoDB cluster</center>

Raspberry Pi 4 is finally here. Start the toss!

Today we combine Scrapy to toss MongoDB cluster!


&emsp;&emsp;MongoDB is a cross-platform, document-oriented database. It is the most popular kind of NoSQL database products. It is a product between relational and non-relational databases. The data structure it supports is very loose, similar to the json format, which can store more complex data types.
&emsp;&emsp;Mongodb has three cluster modes: Master-Slaver mode, Replica Set mode, and sharding mode. Replica set is the most widely used.
&emsp;&emsp;Replica Set is a cluster composed of a group of MongoDB instances, consisting of a master (Primary）Node and multiple backup (Secondary) nodes. Through Replication, the updated data is synchronized by the Primary to other instances, so that each MongoDB instance has the same copy of the data set. When the master node crashes, the backup node will automatically upgrade the member with the highest weight to the new master node; when the cluster has an even number of units, especially with a master-slave architecture, an Arbiter node needs to be added to participate in the upgrade vote. . In the Replica Set operation, generally read and write data are on the primary (Primary) node, and you need to manually specify the backup (Secondary) node of the read library to achieve load balancing.
&emsp;&emsp;Replica Set can realize remote data backup, read-write separation and automatic failover by maintaining redundant database copies.
&emsp;&emsp; Next, we will build a MongoDB one-master-slave Replica Set cluster on Raspberry pi 4, and combine the pre-completed Douban movie crawler to test and verify the Replica Set cluster.

1. System configuration
1.1 Install MongoDB

&emsp;&emsp;We use the apt-get command to install.

      sudo apt-get install mongodb

&emsp;&emsp;After the installation is complete, confirm whether the MongoDB service is normal.

      pi@raspberrypi:~$ mongo
MongoDB shell version: 2.4.14
      connecting to: test
      Server has startup warnings:
      Mon Nov 18 09:01:41.527 [initandlisten]
      ......
>
 
&emsp;&emsp; If the above prompt appears, it means that the MongoDB database is working normally.

&emsp;&emsp;Because there is only one Raspberry Pi 4, in order to practice the construction of multiple servers, a ubuntu 14.04 computer is added as a backup (Secondary) node to build a cluster. In order to ensure the consistency of MongoDB, MongoDB 2.4.14 version is also installed on the ubuntu 14.04 computer. Find linux/mongodb-linux-x86_64-2.4.14.tgz on www.mongodb.org/dl/linux, download and install.

2. Build a ReplicaSet cluster
2.1 Server allocation
&emsp;&emsp; In a Replica Set cluster with a master-slave architecture, three roles are required: a primary (Primary) node, a backup (Secondary) node, and an arbitration (Arbiter) node.
&emsp;&emsp; We build the Primary node and Arbiter node on Raspberry Pi 4, and build the Secondary node on the Ubuntu 14.04 computer.
&emsp;&emsp;The IP address of Raspberry Pi 4 is: 192.168.1.3, and the IP address of the ubuntu 14.04 computer is: 192.168.1.8.

2.2 Create a configuration file
&emsp;&emsp; Create the configuration directory mongo_repset under /home/pi, and create the master and arbiter directories in the directory to store configuration files and data.

      pi@raspberrypi:~$ cd mongo_repset/
      pi@raspberrypi:~/mongo_repset$ ls
      arbiter master
&emsp;&emsp;Primary node configuration file:

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

&emsp;&emsp;Arbiter node configuration file:

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

&emsp;&emsp; Create a configuration directory mongo_repset under /home/pp on the ubuntu 14.04 computer, and create a slave directory in the directory to store configuration files and data.

pp@pp-ThinkPad-S2-2nd-Gen:~/mongo_repset$ ls
slave
&emsp;&emsp;Backup (Secondary) node configuration file:

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

&emsp;&emsp;Parameter description:
&emsp;&emsp;dbpath: database data storage directory
&emsp;&emsp;logpath: database log storage directory
&emsp;&emsp;pidfilepath: the directory where the database pid file is stored
&emsp;&emsp;keyFile: used to verify files between nodes, the content of the files on each node must be consistent, the file permissions must be 600, only the Replica Set mode is valid
&emsp;&emsp;directoryperdb: Whether the database is stored in directories
&emsp;&emsp;logappend: log file appended storage
&emsp;&emsp;replSet: The name of the Replica Set, we define it as movies
&emsp;&emsp;bind_ip: the ip address bound by mongodb
&emsp;&emsp;port: port
&emsp;&emsp;auth: Whether to enable authentication
&emsp;&emsp;oplogSize: Set the size of the oplog file (MB)
&emsp;&emsp;fork: the daemon is running, creating a process
&emsp;&emsp;moprealloc: Whether to disable data file preallocation
&emsp;&emsp;maxConns: Maximum number of connections, default 2000

&emsp;&emsp;The keyFile and auth options should be configured in the cluster, and then enable after adding authenticated users.

2.3 Start MongoDB
&emsp;&emsp; Start the MongoDB service on Raspberry Pi 4 and Ubuntu 14.04 computers respectively.

pi@raspberrypi:~/mongo_repset$ mongod -f ./master/mongodb_master.conf
pi@raspberrypi:~/mongo_repset$ mongod -f ./arbiter/mongodb_arbiter.conf
pp@pp-ThinkPad-S2-2nd-Gen:~/mongo_repset$ mongod -f ./salve/mongodb_slave.conf
&emsp;&emsp; If an error occurs when starting the MongoDB service, you can check the log file in the corresponding directory to find the specific cause of the error.

2.4 Configure the cluster
&emsp;&emsp; The cluster needs to be performed on the primary (Primary) node.
&emsp;&emsp; Connect to the MongoDB of the primary (Primary) node:

pi@raspberrypi:~/mongo_repset$ mongo 192.168.1.3:27017
MongoDB shell version: 2.4.14
connecting to: 192.168.1.3:27017/test
>

&emsp;&emsp; Configure cluster parameters:

> use admin
      switched to db admin
> cfg={ _id:"movies", members:[ {_id:0,host:'192.168.1.3:27017',priority:2}, {_id:1,host:'192.168.1.8:27017',priority: 1}, {_id:2,host:'192.168.1.3:27019',arbiterOnly:true}] };
{
          "_id": "movies",
          "members": [
              {
                  "_id": 0,
                  "host": "192.168.1.3:27017",
                  "priority": 2
              },
              {
                  "_id": 1,
                  "host": "192.168.1.8:27017",
                  "priority": 1
              },
              {
                  "_id": 2,
                  "host": "192.168.1.3:27019",
                  "arbiterOnly": true
              }
          ]
}
> rs.initiate(cfg)
{
          "info": "Config now saved locally. Should come online in about a minute.",
          "ok": 1
}

&emsp;&emsp;Remarks:
&emsp;&emsp; The cfg name of the cluster configuration can be customized, as long as it does not conflict with the mongodb parameter, the _id parameter is the Replica Set name, the priority value in members is the primary node with the higher priority value, and the arbitration (Arbiter) point must be ArbiterOnly:true must be added, otherwise the active/standby mode will not take effect.
&emsp;&emsp;Cluster cfg configuration takes effect: rs.initiate(cfg)

&emsp;&emsp; After the cluster configuration takes effect, let's check the cluster status: rs.status()

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
&emsp;&emsp;You can see that the cluster status is normal, where "stateStr": "PRIMARY" represents the primary (Primary) node, "stateStr": "SECONDARY" represents the backup (Secondary) node, and "stateStr": "ARBITER, represents the arbitration (Arbiter) node.

2.5 cluster verification
The &emsp;&emsp; cluster is set up, and then we use the method of stopping/restarting the primary (Primary) node to see if the cluster can normally switch between the primary and standby nodes.
&emsp;&emsp; directly kill the mongod process of the primary node on the Raspberry Pi 4, and then connect to the secondary node of ubuntu 14.04 to query the cluster status.

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
&emsp;&emsp;You can see that the state of the original primary (Primary) node in the cluster has changed to "stateStr": "(not reachable/healthy)", and the state of the original backup (Secondary) node has changed to "stateStr": "PRIMARY" , Becomes the new primary (Primary) node.
&emsp;&emsp; After restarting the primary (Primary) node on the Raspberry Pi 4, the cluster status is queried and it is restored to the original status.
&emsp;&emsp;From the above verification, you can see that the active and standby nodes of the cluster are switched normally.

2.6 Configure keyfile
&emsp;&emsp; In order to ensure the security between clusters, it is necessary to increase the KeyFile security authentication mechanism, that is, the keyFile configuration item commented out when creating the configuration file in chapter 2.2.

&emsp;&emsp; uses keyfile authentication, each mongod instance in the replica set uses the keyfile content to authenticate other members. Only mongod instances with the correct keyfile can be added to the replica set. The content of the keyfile must be 6 to 1024 characters in length, and the keyfile content of all members of the replica set must be the same.

&emsp;&emsp; Enabling keyfile authentication will enable auth authentication by default. The user's auth authentication is required to connect to the MongoDB database, so you also need to create a user.

&emsp;&emsp;We first create users in the cluster and authenticate them in the admin database.


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

&emsp;&emsp; After the user is created, shut down the services of the active and standby nodes and arbiter nodes, and you can directly kill the process.
&emsp;&emsp; Create a keyfile on Raspberry Pi 4 and modify permissions.

      pi@raspberrypi:~/mongo_repset$ openssl rand -base64 128> ./mongodb.key
      pi@raspberrypi:~/mongo_repset$ chmod 600 ./mongodb.key
After &emsp;&emsp; is created, copy the keyfile to the ubuntu 14.04 machine.
&emsp;&emsp; Modify the configuration file of each node, open the keyFile and auth configuration items that were originally commented out, and restart each node. When restarting the service, you may encounter the following errors:

invalid char in key file /home/pi/mongo_repset/mongodb.key: =
&emsp;&emsp;This is because there is a'=' character at the end of the keyFile content, you can edit the keyFile file and delete it directly. This error is related to the version of MongoDB.

&emsp;&emsp; Reconnect to the primary node.


	 pi@raspberrypi:~/mongo_repset$ mongo 192.168.1.3:27017/admin
MongoDB shell version: 2.4.14
connecting to: 192.168.1.3:27017/admin
> rs.status()
{"ok": 0, "errmsg": "unauthorized"}
&emsp;&emsp;If you connect to MongoDB without user authentication, you will not be able to view the cluster status.

pi@raspberrypi:~/mongo_repset$ mongo 192.168.1.3:27017/admin -u root -p root
MongoDB shell version: 2.4.14
connecting to: 192.168.1.3:27017/admin
......
movies:PRIMARY> rs.status()
{
          "set": "movies",
          "date": ISODate("2019-11-22T12:04:59Z"),
          "myState": 1,
          "members": [
              {
                  "_id": 0,
                  "name": "192.168.1.3:27017",
                  "health": 1,
                  "state": 1,
                  "stateStr": "PRIMARY",
                  .......
&emsp;&emsp;User authentication connects to MongoDB, you can see the cluster status normally.

&emsp;&emsp;So far, the replica set of MongoDB has been built.
3. Replica set verification
&emsp;&emsp; We use Douban movie crawler to verify the data synchronization of the replica set.
3.1 Modify the MongoDB operation code of the crawler
&emsp;&emsp;The operation code of MongoDB is in pipelines.py. After crawling the Douban movie data, store the data in the movie-infos database.

      from pymongo import ReadPreference

ReplicaSet = True #Connect the replica set: True


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

3.2 Verification crawler
&emsp;&emsp;On the command line, run scrapy crawl douban, and the crawler will start working!
&emsp;&emsp;Let’s take a look at the results of the crawler.
 
&emsp;&emsp; Connect to the primary node of the cluster and enter the operation interface.
&emsp;&emsp;Use the "show dbs" command to view the database, the movie_infos database has been created.

movies:PRIMARY> show dbs;
admin 0.03125GB
local 0.15625GB
movie_infos 0.03125GB
 
&emsp;&emsp;Enter the movie_infos database, use the "show collections" command to view collections, collection movies is successfully created.

movies:PRIMARY> use movie_infos
      switched to db movie_infos
      movies:PRIMARY> show collections;
      movies
      system.indexes

&emsp;&emsp;View the data in collection movies.
      
movies:PRIMARY> db.movies.find()
      {"_id": ObjectId("5dd7e9b874fece69b4d1c70f"), "moviename": "A story sadder than sadness is sadder story", "year": "2018", "info": "\n Director: Lin Xiaoqian\ n Screenwriter: Lu Anxian\n Starring: Chen Yihan/ Liu Yihao/ Zhang Shuhao/ Chen Tingni/ Wu Yingjie/ He Haochen/ You Daqing/ Shi Zhitian/ Huang Liling/ Yao Aining\n Genre: Love\n \n Production country/region: Taiwan, China\n Language : Mandarin Chinese\n Release date: 2018-11-30 (Taiwan, China) / 2019-03-14 (Mainland China)\n Duration: 105 minutes\n Also known as: More Than Blue\n IMDb link: tt9081562\n \n",
      "stars": "4.8", "synopsis": "Record producer Zhang Zhekai (Liu Yihao) and ace songwriter Song Yuanyuan (Chen Yihan) depended on each other for fate. The two had only been partners since childhood. They were relatives and friends. It was the other half of fate. Zhe Kai, whose father suffered from a serious genetic illness and was abandoned by his mother, was afraid that he would be sick at any time and die soon. He never crossed the boundaries of friendship to show love to Yuanyuan. Seeing Zhe Kai’s illness worsened, he Secretly decided to use the remaining life to complete the finale between them, and then find a good man for Yuanyuan who can entrust her life. At this time, the gentle and considerate doctor (Zhang Shuhao) appeared in a timely manner and made him a caring for Yuanyuan. The best candidates, the two are developing the relationship step by step. Everything seems to be carried out under Zhe Kai's plan. However, the story is far more sad than what is written here..."}
      {"_id": ObjectId("5dd7e9b974fece69b4d1c710"), "moviename": "A Dog's Journey 2 A Dog's Journey", "year": "2019", "info": "\n Director: Gail Mancuso \n Screenwriter: W. Bruce Cameron/ Maya Forbes/ Catherine Mike/ Wallace Volodowski\n Starring: Dennis Quaid/ Catherine Prescott/ Liu Xianhua/ Margot Helgenberger/ Betty Gilpin/ Josh Gad/ Abby Ryder Fterson/ Jack Manley/ Daniela Barbosa/ Chen Qiye/ Jeff Ropp/ Jim ·Kobe\n Genre: Drama/Comedy/Family\n \n Production Country/Region: Mainland China/India/Hong Kong/United States\n Language: English\n Release Date: 2019-05-17 (United States/Mainland China )\n Duration: 108 minutes\n Also known as: Goodbye is also a dog friend 2 (Hong Kong) / A Dog's Journey (Taiwan) / A Dog's Journey / To Meet You 2 / A Dog's Purpose 2\n IMDb link : tt8385474\n\n", "stars": "6.9", "synopsis": "Puppy Bailey continues his mission. Under the instruction of his owner Ethan, through constant life cycles, he persists in guarding Ethan’s granddaughter CJ, Regard Ethan’s love and companionship for his granddaughter as the most important mission and meaning, and ultimately help CJ reap happiness and return to his master Ethan again."}
{"_id": ObjectId("5dd7e9ba74fece69b4d1c711"), "moviename": "Over the Spring", "year": "2018", "info": "\n Director: Bai Xue\n Screenwriter: Bai Xue/ Lin Meiru\n Leading role: Huang Yao/ Sun Yang/ Tongan/ Ni Hongjie/ Jiang Meiyi/ Liao Qizhi/ Jiao Gang\n Genre: Drama\n \n Production Country/Region: Mainland China\n Language: Mandarin Chinese/ Cantonese\n Release Date: March 2019 -15 (Mainland China) / 2018-09-08 (Toronto Film Festival)\n Duration: 99 minutes\n Also known as: Divider / Pepe / The Crossing\n IMDb link: tt8875366\n\n", " stars": "7.7", "synopsis": "Pei Pei (Huang Yao), a 16-year-old female student from a single parent family, lives in both Hong Kong and Shenzhen. She goes to school in Hong Kong during the day and returns to Shenzhen with her mother at night (Ni Hongjie) (Played) live together and frequently travel between the two places. In order to travel with her best friend Joe (Tonga), for her own sense of existence, and for her ignorant affection for Joe’s boyfriend Ahao (Sun Yang), her heart The impulse was ignited, and the "water guest" became another identity for her, and a youthful story with a sense of "adventure" began."}
      ......

&emsp;&emsp; Connect to the cluster backup (Secondary) node and enter the operation interface.
&emsp;&emsp;Use the "show dbs" command to view the database, the movie_infos database has been created.

movies:SECONDARY> show databases;
admin 0.078125GB
local 0.203125GB
movie_infos 0.078125GB

&emsp;&emsp;Enter the movie_infos database and use the "show collections" command to view the collections. The following error will appear. This is because the backup (Secondary) in the replica set is unreadable by default. Just use the rs.slaveOk() command to set it. .

movies:SECONDARY> show collections
Fri Nov 22 22:08:02.275 error: {"$err": "not master and slaveOk=false", "code": 13435} at src/mongo/shell/query.js:128
movies:SECONDARY> rs.slaveOk();

&emsp;&emsp; Re-query, collection movies is successfully created.

movies:SECONDARY> show collections
movies
system.indexes

&emsp;&emsp;Check the data in collection movies, you can see that it is consistent with the data in the primary node.
&emsp;&emsp;The replica set is working properly.

&emsp;&emsp;MongoDB database crawler code, please visit: https://github.com/dangelzjj/enjoy_Raspberry-Pi-4

4. Reference materials
&emsp;&emsp;https://docs.mongodb.com/manual/
&emsp;&emsp;https://docs.mongodb.com/manual/replication/

-----
&emsp;&emsp;Anwei Cloud is a leading cloud technology team based on Arm architecture in China, providing enterprise-level cloud technologies and services such as virtualization, data analysis, data storage, text processing, semantic analysis, and automated scripting.
&emsp;&emsp;For more information, please follow the "Anweiyun" public account.
