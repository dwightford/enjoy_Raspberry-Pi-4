<center>玩转Raspberry Pi 4之Docke容器</center>

Raspberry Pi 4终于到手了。折腾开始!  

今天我们折腾Docker容器！

&emsp;&emsp;Docker是一个开源的应用容器引擎，我们可以把应用以及依赖包打包到一个镜像中，发布到支持Docker的 Linux或Windows 机器上，实现虚拟化。  
&emsp;&emsp;Docker作为服务器的必备功能，我们在Raspberry Pi 4上来实践一下用Docker容器来安装Nginx。

1.系统配置  
1.1 安装Docker  

    curl -ssl https://get.docker.com | sh  
    
1.2 将pi用户加入docker组  
&emsp;&emsp;默认情况下，Docker 命令使用 Unix socket 与Docker 引擎通讯。只有 root 用户和 docker 组的用户才有权限访问Docker 引擎的 Unix socket。所以需要把pi用户加入 加入 docker 用户组。

	sudo usermod -aG docker pi
1.3 下载nginx镜像  
&emsp;&emsp;我们先搜索nginx镜像。

	sudo docker search nginx
&emsp;&emsp;nginx镜像是存在的。

    pi@raspberrypi:~$ sudo docker search nginx
    NAME                      DESCRIPTION            
    nginx                     Official build of Nginx.                          
    jwilder/nginx-proxy       Automated Nginx reverse proxy for docker con…   
    richarvey/nginx-php-fpm   Container running Nginx + PHP-FPM capable of… 
    linuxserver/nginx         An Nginx container, brought to you by LinuxS… 
    ...... 
 
&emsp;&emsp;下载nginx镜像到本地。

	sudo docker pull nginx

&emsp;&emsp;docker pull结束后，我们用docker images命令看看下载是否成功。  

    pi@raspberrypi:~$ docker images
    REPOSITORY    TAG       IMAGE ID        CREATED        SIZE
    nginx         latest    f8150062ad27    2 weeks ago    97.7MB
 
&emsp;&emsp;nginx镜像已经存在，下载成功。

2.配置安装nginx服务  
2.1 配置默认nginx WEB服务  
&emsp;&emsp;用docker run命令来启动默认配置的nginx容器实例。  

	sudo docker run --name nginx-test -p 8051:80 -d nginx
&emsp;&emsp;-name参数：容器命名为nginx-test   
&emsp;&emsp;-p参数： 端口映射，将本地8051端口映射到容器内部的80端口  
&emsp;&emsp;-d参数：设置容器在在后台一直运行  
&emsp;&emsp;命令执行完后，会打印容器ID，用docker ps命令可以查看到容器已经在运行。  

    pi@raspberrypi:~$ docker ps 
    CONTAINER ID   IMAGE   COMMAND                  CREATED        STATUS          PORTS                  NAMES
    c2bd7915a7b8   nginx   "nginx -g 'daemon of…"   Up 10 seconds  Up 6 seconds    0.0.0.0:8051->80/tcp   nginx-test
&emsp;&emsp;用浏览器访问web服务http://localhost:8051，看到Nginx的web服务已经启动。
 
2.2 配置自定义WEB服务  
&emsp;&emsp;docker run命令可以用-v 参数把容器实例里的服务目录映射为本地目录。  
&emsp;&emsp;我们用docker exec命令进入容器实例来看一下nginx WEB服务的目录。  

    sudo docker exec -it c2bd7915a7b8 /bin/bash
&emsp;&emsp;进入容器实例，找到nginx WEB服务的HTML目录为：/usr/share/nginx/html   
&emsp;&emsp;nginx服务的配置文件目录为：/etc/nginx/nginx.conf  
&emsp;&emsp;nginx服务的log目录为：/var/log/nginx

&emsp;&emsp;我们以HTML目录为例来验证目录映射。  
&emsp;&emsp;在/home/pi目录下创建自定义目录/docker/nginx/testpage，创建自定义网页index.html，我们在index.html中打印 “Just a test!!!”，进行功能验证。
 
&emsp;&emsp;用docker stop命令停止存在的nginx容器实例。  
&emsp;&emsp;重新创建docker镜像实例，并映射HTML网页的目录。  

    sudo docker run --name nginx-test-1 -v /home/pi/docker/nginx/testpage/:/usr/share/nginx/html -p 8052:80 -d nginx
 
&emsp;&emsp;新建的nginx-test-1实例已经创建成功并启动。  

    pi@raspberrypi:~$ docker ps 
    CONTAINER ID   IMAGE   COMMAND                  CREATED        STATUS                       PORTS                  NAMES
    2904ef49cf38   nginx   "nginx -g 'daemon of…"   Up 7 seconds   Up 9 seconds                 0.0.0.0:8052->80/tcp   nginx-test-1
    c2bd7915a7b8   nginx   "nginx -g 'daemon of…"   Up 15 minutes  Exited (0) 50 seconds ago    0.0.0.0:8051->80/tcp   nginx-test
&emsp;&emsp;用浏览器访问web服务http://localhost:8052，看到浏览器页面显示“Just a test!!!”，nginx WEB服务的HTML目录映射成功。

3.docker集群  
&emsp;&emsp;docker支持用docker swarm命令来管理docker集群。  
&emsp;&emsp;docker集群是指通过把多个docker engine聚集在一起，形成一个大的docker engine，对外提供容器的集群服务。同时这个集群对外提供Swarm API，用户可以像使用docker engine一样使用docker集群。  
&emsp;&emsp;由于只有一台Raspberry Pi 4， 因此加上另外一台安装好docker的ubuntu电脑，来配置docker swarm集群。其中Raspberry Pi 4作为manager节点，ubuntu电脑作为worker节点。其中：  
&emsp;&emsp;Raspberry Pi 4的ip地址是： 192.168.1.8  
&emsp;&emsp;ubuntu机器的ip地址是： 192.168.1.9  

3.1 初始化swarm  
&emsp;&emsp;在Raspberry Pi 4上初始化swarm。

    pi@raspberrypi:~$ sudo docker swarm init
    Swarm initialized: current node (yyhzfgpll80oshvze4j9bqntm) is now a manager.

    To add a worker to this swarm, run the following command:

        docker swarm join --token SWMTKN-1-3bgerg7flasaux1gwr7was3afecm0909e6lfqu7jrqgij0qwi0-429z4k8sbngv0cj38pqsfdza7 192.168.1.2:2377

    To add a manager to this swarm, run 'docker swarm join-token manager' and follow the instructions.
 
&emsp;&emsp;初始化结束后，会生成集群token，这个token是该集群的唯一标记。worker节点需要用这个集群token来加入到集群中。  

3.2 添加worker节点  
&emsp;&emsp;在ubuntu机器上执行Raspberry Pi 4上docker swarm初始化时出现的docker swarm join命令，把ubuntu机器作为worker节点加入到集群。

    pp@pp-ThinkPad-S2-2nd-Gen:~$ docker swarm join --token SWMTKN-1-3bgerg7flasaux1gwr7was3afecm0909e6lfqu7jrqgij0qwi0-429z4k8sbngv0cj38pqsfdza7 192.168.1.2:2377
    This node joined a swarm as a worker.
 
&emsp;&emsp;在Raspberry Pi 4上查看集群内的节点，可以看到有了两个节点。

    pi@raspberrypi:~$ docker node ls
    ID                            HOSTNAME                 STATUS     AVAILABILITY     MANAGER STATUS   ENGINE VERSION
    rpkri58dvtt0e701im76v9xzy     pp-ThinkPad-S2-2nd-Gen   Ready      Active                            19.03.4
    yyhzfgpll80oshvze4j9bqntm *   raspberrypi              Ready      Active           Leader           19.03.4


&emsp;&emsp;如果要添加其他manager节点，token与工作节点的字符串不同。需要在当前manager节点上执行以下命令：  

    pi@raspberrypi:~$ docker swarm join-token manager
    To add a manager to this swarm, run the following command:

    docker swarm join --token SWMTKN-1-3bgerg7flasaux1gwr7was3afecm0909e6lfqu7jrqgij0qwi0-41ybbx13dm7klq9zcmb2x7xq4 192.168.1.2:2377

&emsp;&emsp;并在新增的manager节点执行docker swarm join命令。  
&emsp;&emsp;由于目前只有两个节点，所以不添加额外的manager节点。

3.3 创建集群服务  
&emsp;&emsp;我们给集群创建nginx WEB服务，创建命令如下：  

    docker service create --replicas 2 -p 8053:80 --name nginx-test-2 nginx
&emsp;&emsp;其中：  
&emsp;&emsp;-replicas 参数：指运行实例个数，集群中有两个节点，因此设置为2  
&emsp;&emsp;-p参数：端口映射，将集群中节点的8053端口映射到容器内部的80端口  
&emsp;&emsp;--name参数：集群服务的名称，设置为nginx-test-2  
&emsp;&emsp;最后一个参数nginx是指使用的nginx镜像

    pi@raspberrypi:~$ docker service create --replicas 2 -p 8053:80 --name nginx-test-2 nginx
    0qvotc2gi19n2f6pqp7q2r4fs
    overall progress: 2 out of 2 tasks 
    1/2: running   [==================================================>] 
    2/2: running   [==================================================>] 
    verify: Service converged 
 
&emsp;&emsp;创建完成后，可以用docker service ls命令查看service。  

    pi@raspberrypi:~$ docker service ls
    ID            NAME          MODE          REPLICAS     IMAGE          PORTS
    0qvotc2gi19n  nginx-test-2  replicated    2/2          nginx:latest   *:8053->80/tcp
 
&emsp;&emsp;在manager节点Raspberry Pi 4上查看nginx容器实例：  

    pi@raspberrypi:~$ sudo docker ps -a
    CONTAINER ID    IMAGE           COMMAND                  CREATED          STATUS                     PORTS       NAMES
    c32f6bd0625f    nginx:latest    "nginx -g 'daemon of…"   5 minutes ago    Up 5 minutes               80/tcp      nginx-test-2.2.ql90wmzklbxa8woocuckmuak3
    2904ef49cf38    nginx           "nginx -g 'daemon of…"   8 hours ago      Exited (0) 6 minutes ago               nginx-test-1
    c2bd7915a7b8    nginx           "nginx -g 'daemon of…"   8 hours ago      Exited (0) 5 hours ago                 nginx-test
 
&emsp;&emsp;可以看到新的nginx容器实例创建成功。
    用浏览器访问manager节点上新建的nginx WEB服务，http://192.168.1.8:8053，成功！
 
&emsp;&emsp;在worker节点ubuntu机器上查看nginx容器实例：  

    pp@pp-ThinkPad-S2-2nd-Gen:~$ docker ps -a
    CONTAINER ID    IMAGE           COMMAND                  CREATED          STATUS           PORTS       NAMES
    1c0e985762c1    nginx:latest    "nginx -g 'daemon of…"   13 minutes ago   Up 13 minutes    80/tcp      nginx-test-2.1.qi5ryylc60e99y5307akjxcwm
 
&emsp;&emsp;可以看到nginx容器实例创建成功。
&emsp;&emsp;用浏览器访问worke节点上的nginx WEB服务，http://192.168.1.9:8053，成功！
 
&emsp;&emsp;至此， docker swarm集群创建并配置成功。  
&emsp;&emsp;对于docker swarm集群的WEB服务，可以再用一台机器来配置nginx负载均衡服务器，用于屏蔽集群中不同IP的节点。nginx负载均衡服务器不在本文讨论范围内，不在此赘述。

3.4 安装docker集群图形化显示工具  
&emsp;&emsp;Visualizer是非常好用的docker swarm集群图形化显示工具，它能非常直观地显示集群中，服务器的状态和服务器上面运行容器的状态。  

3.4.1 下载Visualizer  
&emsp;&emsp;下载之前，可以用sudo docker search visualizer命令来搜索镜像。  

    pi@raspberrypi:~$ sudo docker search visualizer
    NAME                         DESCRIPTION                                     STARS       OFFICIAL    AUTOMATED
    dockersamples/visualizer                                                     108                                     
    alexellis2/visualizer-arm    Visualizer for Docker Swarm                     20                                      
    bretfisher/visualizer        Clone of dockersamples/visualizer for my Doc…   9                       [OK]
    hypriot/visualizer           Docker Swarm Visualizer for different CPU ty…   5                                       
    ......
  
&emsp;&emsp;因为Raspberry Pi系统采用ARM芯片，所以镜像要采用alexellis2/visualizer-arm。  
&emsp;&emsp;下载镜像：  
    
    sudo docker pull alexellis2/visualizer-arm
3.4.2 配置安装visualizer服务  
&emsp;&emsp;visualizer服务也是用docker run命令来配置，与配置docker的nginx服务类似。我们用8060端口来映射visualizer容器内部的 8080 端口。  

    sudo docker run -it -d -p 8060:8080 -v /var/run/docker.sock:/var/run/docker.sock alexellis2/visualizer-arm

&emsp;&emsp;服务启动后，查看docker容器实例。

    pi@raspberrypi:~$ sudo docker ps -a
    CONTAINER ID    IMAGE                       COMMAND                  CREATED              STATUS                     PORTS                    NAMES
    cb6ad67b4e4d    alexellis2/visualizer-arm   "/usr/bin/entry.sh n…"   About a minute ago   Up About a minute          0.0.0.0:8060->8080/tcp   fervent_moser
    c32f6bd0625f    nginx:latest                "nginx -g 'daemon of…"   25 minutes ago       Up 25 minutes              80/tcp                   nginx-test-2.2.ql90wmzklbxa8woocuckmuak3
    2904ef49cf38    nginx                       "nginx -g 'daemon of…"   8 hours ago          Exited (0) 6 minutes ago                            nginx-test-1
    c2bd7915a7b8    nginx                       "nginx -g 'daemon of…"   8 hours ago          Exited (0) 5 hours ago                              nginx-test
&emsp;&emsp;如果在有多个manager节点的docker swarm集群中，可以创建visualizer service。  

    docker service create \
    --name=viz \
    --publish=8060:8080/tcp \
    --constraint=node.role==manager \
    --mount=type=bind,src=/var/run/docker.sock,dst=/var/run/docker.sock \
    alexellis2/visualizer-arm
3.4.3 访问visualizer服务  
&emsp;&emsp;用浏览器访问visualizer服务：http://192.168.1.8:8060/，能看到服务界面。配置成功！


4.参考资料:  
&emsp;&emsp;https://www.raspberrypi.org/blog/docker-comes-to-raspberry-pi/  
&emsp;&emsp;https://hub.docker.com/r/dockersamples/visualizer/

-
&emsp;&emsp;安微云是国内领先的基于Arm架构的云技术团队，提供虚拟化、数据分析、数据存储、文本处理、语义分析、自动化脚本等企业级云技术及服务。  
&emsp;&emsp;更多信息，请关注"安微云"公众号。