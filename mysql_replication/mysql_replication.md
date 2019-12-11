<center>玩转Raspberry Pi 4之MySQL Replication</center>

Raspberry Pi 4终于到手了。折腾开始!  

今天我们折腾MySQL数据库Replication主从架构！

&emsp;&emsp;MySQL是最流行的关系型数据库管理系统之一，也是服务器系统的必备组件之一。对于一个服务系统来说，单一的MySQL数据库服务器风险巨大。如果这台服务器出现宕机或者异常错误，会导致整个服务不可用，甚至导致不可恢复的数据丢失。另外随着业务量的加大，单个数据库服务器肯定会出现无法满足访问需求的情况。因此一般需要搭建MySQL数据库集群来保证数据库服务器的高可用性和可扩展性。  
&emsp;&emsp;MySQL数据库集群方案有多种，适应不同的使用场景和发展阶段，常用的方案有Replication主从架构、DBProxy、MHA+ProxySQL、Zookeeper等。一般业务的起步阶段，可以先配置Replication主从架构，后续根据业务的增长来调整MySQL数据库集群方案。  
&emsp;&emsp;在Raspberry pi 4的安装源上并没有MysQL，但有MariaDB。MariaDB的目的是完全兼容MySQL，包括API和命令行。我们就在Raspberry pi 4上实践MariaDB配置Replication主从架构。

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

2.配置MariaDB多实例  
&emsp;&emsp;最基本的Replication主从架构需要一主一从两台服务器。因为只有一台Raspberry Pi 4，我们就配置多实例来启动两个MariDB实例，来配置一主一从的Replication架构。  
2.1 创建多实例数据存放目录  
&emsp;&emsp;配置MariDB多实例就无法使用安装时默认的配置，因此需要创建目录来存放每个实例的数据库文件。  
&emsp;&emsp;我们在3306和3307两个端口上启动MariDB实例，因此在"/home/pi"目录下创建mysql目录，并分别创建3306和3307两个子目录分别存放两个实例的数据。目录创建完成后，还需要修改mysql目录的用户权限给mysql用户。  

      pi@raspberrypi:~$ mkdir mysql
      pi@raspberrypi:~$ mkdir mysql/3306
      pi@raspberrypi:~$ mkdir mysql/3306/data
      pi@raspberrypi:~$ mkdir mysql/3307
      pi@raspberrypi:~$ mkdir mysql/3307/data
      pi@raspberrypi:~$ sudo chown -R mysql:mysql mysql
      pi@raspberrypi:~$ cd mysql
      pi@raspberrypi:~/mysql$ ls
      3306  3307

2.2 初始化多实例数据库  
&emsp;&emsp;数据库存放目录创建好之后，在对应的目录中初始化数据库。  

      pi@raspberrypi:~$ sudo mysql_install_db --basedir=/usr --datadir=/home/pi/mysql/3306/data/ --user=mysql
      pi@raspberrypi:~$ sudo mysql_install_db --basedir=/usr --datadir=/home/pi/mysql/3307/data/ --user=mysql
&emsp;&emsp;数据库初始化命令中的参数含义为:  
&emsp;&emsp;basedir: 表示MariDB的安装目录  
&emsp;&emsp;datadir: 表示数据存放目录  
&emsp;&emsp;user: 表示mysqld服务的运行用户  

2.3 创建多实例配置文件  
&emsp;&emsp;我们用mysqld_multi命令来启动多实例。在mysql目录下创建MariDB多实例配置文件my.cnf。  

      [mysqld_multi]
      mysqld     = /usr/bin/mysqld_safe
      mysqladmin = /usr/bin/mysqladmin
      user       = root
      password   = 123456
      log        = /home/pi/mysql/mysqld_multi.log
      
      [mysqld1]
      port                      = 3306
      socket                    = /home/pi/mysql/3306/mysql.sock
      pid_file                  = /home/pi/mysql/3306/mysql.pid
      basedir                   = /usr
      datadir                   = /home/pi/mysql/3306/data/
      
      # LOGGING
      long_query_time           = 5
      slow_query_log            = 1
      log_error                 = /home/pi/mysql/3306/error.log
      slow_query_log_file       = /home/pi/mysql/3306/slow_query.log
      log_warnings              = 1
      
      # INNODB
      innodb_data_home_dir      = /home/pi/mysql/3306/data
      innodb_buffer_pool_size   = 64M
      innodb_log_file_size      = 64M
      innodb_data_file_path     = ibdata1:12M:autoextend:max:64M
      
      # REPLICATION
      server-id                 = 3306
      log-bin                   = /home/pi/mysql/3306/mysql-binlog
      binlog-do-db              = musics
      
      [mysqld2]
      port                      = 3307
      socket                    = /home/pi/mysql/3307/mysql.sock
      pid_file                  = /home/pi/mysql/3307/mysql.pid
      basedir                   = /usr
      datadir                   = /home/pi/mysql/3307/data/
      
      # LOGGING
      long_query_time           = 5
      slow_query_log            = 1
      log_error                 = /home/pi/mysql/3307/error.log
      slow_query_log_file       = /home/pi/mysql/3307/slow_query.log
      log_warnings              = 1
      
      # INNODB
      innodb_data_home_dir      = /home/pi/mysql/3307/data
      innodb_buffer_pool_size   = 64M
      innodb_log_file_size      = 64M
      innodb_data_file_path     = ibdata1:12M:autoextend:max:64M
      
      # REPLICATION
      server-id                 = 3307
      log-bin                   = /home/pi/mysql/3307/mysql-binlog
&emsp;&emsp;配置文件中配置了mysqld1和mysqld2两个实例的参数。INNODB节中的buffer size可以根据需要进行调整。REPLICATION节中的参数用于配置Replication主从架构，其中server-id字段表示各个实例的id，必须唯一，我们直接取各个实例的端口号为id；log-bin字段启用binary log文件，指示文件路径。  

2.3 启动多实例  
&emsp;&emsp;我们用mysqld_multi命令来启动多实例。启动前需要用ps命令确认一下是否有MariDB进程启动，如果有的话，需要先kill掉。  

      pi@raspberrypi:~/mysql$ ps -A | grep "mysql"
      pi@raspberrypi:~/mysql$ sudo mysqld_multi --defaults-file=./my.cnf  start
      Wide character in print at /usr/bin/mysqld_multi line 606.
&emsp;&emsp;多实例启动后，我们用lsof命令看看3306和3307端口的服务器是否已经启动。  

      pi@raspberrypi:~/mysql$ sudo lsof -i:3306
      COMMAND  PID  USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
      mysqld  5847 mysql   25u  IPv4  32930      0t0  TCP localhost:mysql       (LISTEN)
      mysqld  5847 mysql   46u  IPv4  32932      0t0  TCP localhost:mysql->localhost:47660 (ESTABLISHED)
      mysqld  5848 mysql   49u  IPv4  30488      0t0  TCP localhost:47660->localhost:mysql (ESTABLISHED)
      pi@raspberrypi:~/mysql$ sudo lsof -i:3307
      COMMAND  PID  USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
      mysqld  5848 mysql   23u  IPv4  31207      0t0  TCP localhost:3307 (LISTEN)
&emsp;&emsp;可以看到两个端口上的MariDB实例都正常启动。  

3.配置Replication主从架构  
&emsp;&emsp;Replication是通过binary log文件同步主数据库(Master)上的所有改变到从数据库(Slave)。  

&emsp;&emsp;Replication主从复制过程为：  
&emsp;&emsp;1) 数据发生变化时，Master将数据变更的事件记录到binary log文件；  
&emsp;&emsp;2) Master发送信号，唤醒Dump线程，通知有新事件产生；  
&emsp;&emsp;3) Dump线程将新事件发送给Slave的I/O线程；  
&emsp;&emsp;4) Slave的I/O线程将接受到事件记录到relay log文件；  
&emsp;&emsp;5) Slave的SQL线程从relay log文件中读取事件；  
&emsp;&emsp;6) Slave的SQL线程执行读取的事件，从而实现备库数据的更新。  
&emsp;&emsp;从上面的过程来看，Replication是一个异步过程，会导致在同一时间点从库上的数据可能与主库的不一致，并且无法保证主备之间的延迟，这是Replication架构的一个缺陷。配置为读写分离的服务，有时候在主数据库上写入数据后，从从库上读数据失败，就是这个原因。  

3.1 指定连接数据库实例的用户名  
&emsp;&emsp;MariDB实例正常启动后，在3306和3307目录中会分别生成连接两个数据库实例的socket文件，我们给两个实例的socket指定连接用户名。  

	  pi@raspberrypi:~/mysql$ mysqladmin -uroot password '123456' -S 3306/mysql.sock
	  pi@raspberrypi:~/mysql$ mysqladmin -uroot password '123456' -S 3307/mysql.sock

3.2 创建Replication复制账号  
&emsp;&emsp;我们把端口为3306的实例作为主服务器，登录主服务器，创建Replication复制账号，并授予REPLICATION SLAVE权限。  

      pi@raspberrypi:~/mysql$ mysql -uroot -p123456 -S 3306/mysql.sock 
      Welcome to the MariaDB monitor.  Commands end with ; or \g.
      ......   
      Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.
      MariaDB [(none)]> CREATE USER 'backup'@'localhost' IDENTIFIED BY '123456';
      Query OK, 0 rows affected (0.001 sec)
      MariaDB [(none)]> GRANT REPLICATION SLAVE ON *.* TO 'backup'@'localhost' IDENTIFIED BY '123456';
      Query OK, 0 rows affected (0.001 sec)

3.3 创建数据库  
&emsp;&emsp;我们在多实例配置文件mysqld1实例的REPLICATION节中指定了执行Replication复制的数据库为musics，因此需要分别连接主实例和从实例，创建musics数据库。  

      MariaDB [(none)]> create database musics;
      MariaDB [(none)]> show databases;
      +--------------------+
      | Database           |
      +--------------------+
      | information_schema |
      | musics             |
      | mysql              |
      | performance_schema |
      | test               |
      +--------------------+
      5 rows in set (0.008 sec)

3.4 配置主从Replication  
&emsp;&emsp;我们首先在主实例中查看master状态。  

      MariaDB [(none)]> show master status \G;
      *************************** 1. row ***************************
                  File: mysql-binlog.000001
              Position: 331
          Binlog_Do_DB: musics
      Binlog_Ignore_DB: 
      1 row in set (0.000 sec)
      
      ERROR: No query specified
&emsp;&emsp;查看命令返回的结果的字段含义为：  
&emsp;&emsp;File: 主数据库记录事件的binary log文件名，在从数据库配置时需要用到；  
&emsp;&emsp;Position: 主数据库记录事件的binary log中的事件位置，会随着数据库的操作不断变化，所以在配置Replication时，一般需要锁定主数据库，配置完之后在解锁。这个参数在从数据库配置时需要用到也需要用到；  
&emsp;&emsp;Binlog-Do-DB: 执行Replication操作的数据库，我们配置为musics数据库；  
&emsp;&emsp;Binlog-Ignore-DB: 忽略Replication操作的数据库，我们没有配置。

&emsp;&emsp;为了避免Position参数发生变化，我们先锁定主数据库。  

      MariaDB [(none)]> use musics;
      Reading table information for completion of table and column names
      You can turn off this feature to get a quicker startup with -A

      Database changed
      MariaDB [musics]> flush tables with read lock;
      Query OK, 0 rows affected (0.001 sec)


&emsp;&emsp;我们把3307端口的实例作为从数据库。连接从数据库，进行配置。  

      pi@raspberrypi:~/mysql$ mysql -uroot -p123456 -S 3307/mysql.sock 
      Welcome to the MariaDB monitor.  Commands end with ; or \g.
      ......   
      Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.
      MariaDB [(none)]> stop slave;
      Query OK, 0 rows affected (0.006 sec)
      
      MariaDB [(none)]> change master to master_host='127.0.0.1', master_user='backup',master_password='123456',master_port=3306,master_log_file='mysql-bin.000003',master_log_pos=1;
      Query OK, 0 rows affected (0.023 sec)
      
      MariaDB [(none)]> start slave; 
      Query OK, 0 rows affected (0.001 sec)

&emsp;&emsp;我们来看一下slave的状态。  

      MariaDB [(none)]> show slave status\G;
      *************************** 1. row ***************************
                Slave_IO_State: Waiting for master to send event
                   Master_Host: localhost
                   Master_User: backup
                   Master_Port: 3306
                 Connect_Retry: 60
               Master_Log_File: mysql-binlog.000004
           Read_Master_Log_Pos: 345
                Relay_Log_File: mysql-relay-bin.000008
                 Relay_Log_Pos: 647
         Relay_Master_Log_File: mysql-binlog.000004
              Slave_IO_Running: Yes
             Slave_SQL_Running: Yes
               Replicate_Do_DB: 
           Replicate_Ignore_DB: 
           ......
&emsp;&emsp;slave状态查询结果中，如果Slave-IO-Running和Slave-SQL-Running的状态都是Yes时，表示主从数据库的Replication正常。Slave-IO-Running表示能连接到主库，并读取主库的binary log到本地，生成本地relay log文件；Slave-SQL-Running表示能读取本地relay log文件，并执行relay log里的SQL命令。  
&emsp;&emsp;如果查询结果中出现1236错误:   

      ......
      Last_IO_Errno: 1236
      Last_IO_Error: Got fatal error 1236 from master when reading data from binary log: 'Could not find first log file name in binary log index file'
      ......

&emsp;&emsp;可以在从库上执行以下操作，即可正常。  

      MariaDB [(none)]> stop slave;
      MariaDB [(none)]> reset slave;
      MariaDB [(none)]> start slave;

&emsp;&emsp;Replication运行正常后，我们把主数据库解锁。  

      MariaDB [(none)]> unlock tables;


4.Replication测试  
&emsp;&emsp;我们在主数据库创建songs和albums两张表，然后到从数据库看是否也会生成这两张表，以测试Replication。  
&emsp;&emsp;连接主数据库，创建表格：  

      MariaDB [musics]> create table tbl_songs(id int, name varchar(16));
      Query OK, 0 rows affected (0.036 sec)
      MariaDB [musics]> create table tbl_albums(id int, name varchar(32));
      Query OK, 0 rows affected (0.035 sec)
      MariaDB [musics]> show tables;
      +------------------+
      | Tables_in_musics |
      +------------------+
      | tbl_albums       |
      | tbl_songs        |
      +------------------+
      2 rows in set (0.001 sec)

&emsp;&emsp;连接从数据库，查看表格：  

      MariaDB [musics]> show tables;
      +------------------+
      | Tables_in_musics |
      +------------------+
      | tbl_albums       |
      | tbl_songs        |
      +------------------+
      2 rows in set (0.001 sec)

&emsp;&emsp;两张表都能看到，Replication功能正常。  


&emsp;&emsp;更多Raspberry Pi 4折腾过程获取请访问：https://github.com/dangelzjj/enjoy_Raspberry-Pi-4


----
&emsp;&emsp;安微云是国内领先的基于Arm架构的云技术团队，提供虚拟化、数据分析、数据存储、文本处理、语义分析、自动化脚本等企业级云技术及服务。  
&emsp;&emsp;更多信息，请关注"安微云"公众号。