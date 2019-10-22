# 用两种方法爬取链家上海二手房的数据  

##### 1、用python自带的URL处理模块urllib库和beautifulsoup4库实现，速度较慢，里面带有较为详细的图片和备注说明，在jupyter notebook下运行即可   

##### 2、用scrapy库和beautifulsoup库实现，速度较快，在PyCharm下打开项目，点击左下角的Terminal，输入scrapy crawl LianjiaSpider -o House.csv 即可  

  
###### 可能需要提前安装的库有：bs4、scrapy，在终端输入以下命令安装即可  
pip install beautifulsoup4  
pip install scrapy  
