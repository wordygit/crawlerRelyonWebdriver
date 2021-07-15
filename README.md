# crawlerRelyonWebdriver
a crawler rely on webdriver

1. python3.6.2
2. 直接使用pip install pypcap是无法完成安装：
		a)需要下载pypcap1.2.0, 安装npcap-1.50(安装过程要选择适配模式)
		b)将WpdPack_4_1_2.zip(如果找不到版本包可以在现在高版本的链接中将版本号修改一下完成下载)解压后的include会lib中到内容
      复制到python安装路径对应的include和lib目录中
    c)搜索旧版本15或14的visual studio，安装过程选择C++ 开发环境即可，不需要安装其他拓展包
3. 去pypcap1.2.0 目录执行python setup.py install