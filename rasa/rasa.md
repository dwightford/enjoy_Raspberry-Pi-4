<center>玩转Raspberry Pi 4之asa</center>

Raspberry Pi 4终于到手了。折腾开始!  

今天我们折腾Rasa！

&emsp;&emsp;Rasa是一套开源的NLP机器学习框架，可以用来构建聊天机器人。  
&emsp;&emsp;作为Rasa的爱好者，我们来看看Raspberry Pi 4上如何搭建Rasa框架，并实践一下Rasa的demo程序。

1.系统配置  
&emsp;&emsp;Rasa官网上说明了目前的Rasa框架需要Python3.6以上版本。Raspberry Pi 4自带Python 2.7.16和Python 3.7.3，我们用命令来确认一下Python3的版本。  

      pi@raspberrypi:~$ python3 --version
      Python 3.7.3
&emsp;&emsp;我们在Python3.7环境中安装Rasa框架。

2.安装Rasa框架  
&emsp;&emsp;在Raspberry Pi 4上安装Rasa框架是个非常耗时的工作，我差点崩溃放弃，：）大家要有点心理准备，可以一边听歌，一边安装。
2.1 选择安装方式
&emsp;&emsp;Rasa官网上的安装指导中列举3中安装方式: 快速安装、step-by-step安装和源码编译安装。  
&emsp;&emsp;作为Rasa的爱好者，后续肯定需要基于Rasa框架实践新的聊天机器人，因此我选择源码编译安装，为后续实践做好准备。  
2.2 修改安装源  
&emsp;&emsp;Python3的组件是通过pip3安装的。实践下来发现，Raspberry Pi 4上默认pip3安装源有两个：
    
      https://www.piwheels.org/
      https://files.pythonhosted.org/
&emsp;&emsp;pip3的默认源安装比较缓慢，可以更换为国内源。  

      mkdir ~/.pip
      vim ~/.pip/pip.conf

&emsp;&emsp;然后把下面两行代码复制进去，并保存。这样就把默认pip源替换为aliyun的源。  

      [global]
      index-url = https://mirrors.aliyun.com/pypi/simple

&emsp;&emsp;国内还有其他pip源：

      清华：https://pypi.tuna.tsinghua.edu.cn/simple
      中国科技大学：https://pypi.mirrors.ustc.edu.cn/simple
      豆瓣：http://pypi.douban.com/simple/
&emsp;&emsp;pip源替换后，实际只替换了pythonhosted.org这个源，安装过程中在piwheels.org上下载的组件包下载缓慢时，可以复制下载URL到迅雷等下载工具中，下载后用U盘或者scp命令拷贝到Raspberry Pi 4中用pip3命令安装。

2.3 源码安装Rasa  
&emsp;&emsp;从github上下载Rasa源码：  

      git clone https://github.com/RasaHQ/rasa.git
&emsp;&emsp;进入rasa目录，安装依赖包：  

      cd rasa
      pip3 install -r requirements.txt
&emsp;&emsp;这是个令人崩溃的耗时过程，安装过程中遇到需要在piwheels.org上下载安装的组件，大概率会出现下载失败的提示，如：  

      requirements.txt (line 18))
      Downloading https://www.piwheels.org/simple/future/future-0.18.2-py3-none-any.whl (491kB)
      95% |██████████████████████████████▊ | 471kB 5.2kB/s eta 0:00:04Exception:
      Traceback (most recent call last):
      File "/usr/share/python-wheels/urllib3-1.24.1-py2.py3-none-any.whl/urllib3/contrib/pyopenssl.py", line 294, in recv_into
      ......

      raise ReadTimeoutError(self._pool, None, 'Read timed out.')
      urllib3.exceptions.ReadTimeoutError: HTTPSConnectionPool(host='www.piwheels.org', port=443): Read timed out.
&emsp;&emsp;遇到这种错误，就不要重试了，直接用迅雷下载whl文件后，拷贝进去安装。

      pip3 install ******.whl

&emsp;&emsp;依赖包中要求"tensorflow==1.14.0"，pip3安装源中的tensorflow组件版本只有2.0.0和1.13.1，无法匹配。  

      ......
      Collecting tensorflow==1.14.0 (from -r ./rasa-master/requirements.txt (line 11))
      Could not find a version that satisfies the requirement tensorflow==1.14.0 (from -r ./rasa-master/requirements.txt (line 11)) (from versions: 0.11.0, 1.12.0, 1.13.1)
      No matching distribution found for tensorflow==1.14.0 (from -r ./rasa-master/requirements.txt (line 11))

&emsp;&emsp;Google的tensorflow中文网站tensorflow.google.cn/install/pip和Piwheel的tensorflow网页www.piwheels.org/simple/tensorflow都没有用于Python3.7的tensorflow whl。众里寻他千百度，终于在github上找到了，感谢lhelontra大神！  

      https://github.com/lhelontra/tensorflow-on-arm/releases
&emsp;&emsp;用迅雷下载文件后，tensorflow组件安装完成。

&emsp;&emsp;历经令人崩溃的N多次组件安装失败、迅雷下载组件安装、重试安装依赖包的循环后，终于requirement.txt中的依赖包都安装成功。

&emsp;&emsp;开始安装Rasa框架：  

      pip3 install -e .
&emsp;&emsp;错误不出意外地又一次出现：
    
      ......
      Requirement already satisfied: hyperframe<6,>=5.2.0 in /home/pi/.local/lib/python3.7/site-packages (from h2==3.*->httpcore==0.3.*->requests-async==0.5.0->sanic~=19.6->rasa==1.5.0a1) (5.2.0)
      Installing collected packages: rasa
      Running setup.py develop for rasa
      Complete output from command /usr/bin/python3 -c "import setuptools, tokenize;__file__='/home/pi/rasa/rasa-master/setup.py';f=getattr(tokenize, 'open', open)(__file__);code=f.read().replace('\r\n', '\n');f.close();exec(compile(code, __file__, 'exec'))" develop --no-deps --user --prefix=:
      usage: -c [global_opts] cmd1 [cmd1_opts] [cmd2 [cmd2_opts] ...]
         or: -c --help [cmd1 cmd2 ...]
         or: -c --help-commands
         or: -c cmd --help
    
      error: option --user not recognized
    
      ----------------------------------------
      Command "/usr/bin/python3 -c "import setuptools, tokenize;__file__='/home/pi/rasa/rasa-master/setup.py';f=getattr(tokenize, 'open', open)(__file__);code=f.read().replace('\r\n', '\n');f.close();exec(compile(code, __file__, 'exec'))" develop --no-deps --user --prefix=" failed with error code 1 in /home/pi/rasa/rasa-master/

&emsp;&emsp;从错误log看，令人比较开心的是依赖包的检查都正确通过了，只是在安装setup.py文件develop模式的时候，出现的命令错误。这个小错误我们就不管了，直接用python3命令安装：  

      pi@raspberrypi:~/rasa/rasa-master$ python3 setup.py develop --user
      ....

      Welcome to Rasa!
      If you have any questions, please visit our documentation page: https://rasa.com/docs/
      or join the community discussions on https://forum.rasa.com/

&emsp;&emsp;终于看到了Welcome的字样，Rasa框架安装成功了！

&emsp;&emsp;这里解释一下python3安装setup.py时候的两种方式：  

      python3 setup.py install
&emsp;&emsp;主要是安装稳定的第三方包，这种包不需要再修改或调试。  

      python setup.py develop
&emsp;&emsp;主要用于安装开发中的组件包，这个包可能会不断修改。采用这种安装方式后，修改组件包后，不需要重新安装。  

3.测试Rasa框架  
&emsp;&emsp;创建Rasa工程:  
    
      rasa init --no-prompt

&emsp;&emsp;出错不出意外的又出现了：  

      pi@raspberrypi:~/rasa/rasaprj$ rasa init --no-prompt
      Welcome to Rasa! 
      ......

      Created project directory at '/home/pi/rasa/rasaprj'.
      Finished creating project structure.
      Training an initial model...
      Training Core model...
      Traceback (most recent call last):
      ......
      ImportError: libf77blas.so.3: cannot open shared object file: No such file or directory
      .......
&emsp;&emsp;查看工程目录，发现自动生成的工程文件都已经存在，缺失需要训练语料才能生成的model目录，应该是训练语料时候缺失依赖库libf77blas.so文件，我们继续安装依赖库。  

      sudo apt-get install libatlas-base-dev

&emsp;&emsp;安装完成后，我们直接调用语料训练命令，错误继续。  

      pi@raspberrypi:~/rasa/rasaprj$ rasa train
      ......
      File "/home/pi/.local/lib/python3.7/site-packages/tensorflow/contrib/__init__.py", line 31, in <module>
      from tensorflow.contrib import cloud
      ImportError: cannot import name 'cloud' from 'tensorflow.contrib' (/home/pi/.local/lib/python3.7/site-packages/tensorflow/contrib/__init__.py)

&emsp;&emsp;查看错误中提到的init.py文件，我们用不到google cloud，简单方法，先把错误代码注释掉。  

      .....
      from tensorflow.contrib import bayesflow
      from tensorflow.contrib import checkpoint
      #if os.name != "nt" and platform.machine() != "s390x":
      #    from tensorflow.contrib import cloud
      from tensorflow.contrib import cluster_resolver
      ......

&emsp;&emsp;修改完成后，我们继续调用语料训练命令，错误也继续。  

      pi@raspberrypi:~/rasa/rasaprj$ rasa train
      ......
      File "/home/pi/.local/lib/python3.7/site-packages/h5py/__init__.py", line 26, in <module>
         from . import _errors
      ImportError: libhdf5_serial.so.103: cannot open shared object file: No such file or directory

&emsp;&emsp;继续安装依赖库:  

      sudo apt-get install libhdf5-dev
&emsp;&emsp;安装完成后，我们继续调用语料训练命令，终于出现了训练过程的界面！  
&emsp;&emsp;训练结束后，查看工程目录，model目录和model文件都正确生成！


&emsp;&emsp;激动人心的时刻到了，我们开始测试工程的聊天机器人：  

      pi@raspberrypi:~/rasa/rasaprj$ rasa shell
      2019-11-13 11:52:13 INFO     root  - Connecting to channel 'cmdline'     which was specified by the '--connector' argument. Any other channels will be ignored. To connect to all given channels, omit the '--connector' argument.
      2019-11-13 11:52:13 INFO     root  - Starting Rasa server on http://localhost:5005
      2019-11-13 11:52:25 INFO     absl  - Entry Point [tensor2tensor.envs.tic_tac_toe_env:TicTacToeEnv] registered with id [T2TEnv-TicTacToeEnv-v0]
      Bot loaded. Type a message and press enter (use '/stop' to exit): 
      Your input ->  hello                                                                                                                                         
      Hey! How are you?
      Your input ->           

&emsp;&emsp;聊天机器人正常工作！

&emsp;&emsp;Rasa的爱好者们，可以在Raspberry Pi 4上玩自己的聊天机器人了！

4.参考资料:  
&emsp;&emsp;https://rasa.com  
&emsp;&emsp;https://rasa.com/docs/rasa/user-guide/installation/  
&emsp;&emsp;https://rasa.com/docs/rasa/user-guide/rasa-tutorial/



----
&emsp;&emsp;安微云是国内领先的基于Arm架构的云技术团队，提供虚拟化、数据分析、数据存储、文本处理、语义分析、自动化脚本等企业级云技术及服务。
更多信息，  
&emsp;&emsp;请关注"安微云"公众号。