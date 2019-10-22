#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: xioccMo
# contact: xioccmo@outlook.com
# software: PyCharm
# file: LianjiaSpider.py
# time: 2019/10/23 1:51

import scrapy
from bs4 import BeautifulSoup
import re
import json


class LianJia(scrapy.Spider):

    name = "LianjiaSpider"

    start_urls = ["https://sh.lianjia.com/ershoufang/"]

    def parse(self, response):

        Soup = BeautifulSoup(response.body, features="html.parser")
        FilitedLabel = Soup.find_all("a", {"href": re.compile("^/ershoufang/"), "title": re.compile("^上海.{2}在售二手房")})
        DistrictLink = [filitedLabel['href'] for filitedLabel in FilitedLabel]

        for districtLink in DistrictLink:
            DistrictUrl = "https://sh.lianjia.com" + districtLink
            yield scrapy.Request(response.urljoin(DistrictUrl), callback=self.parseDistrictPage)

    def parseDistrictPage(self, response):

        district = response.url.split("/")[4]
        Soup = BeautifulSoup(response.body, features="html.parser")
        FilitedLabel = Soup.find_all("a", {"href": re.compile("^/ershoufang/((?!" + district + "/)[^/]*?/)"), "title": None})
        BlockLink = [filitedLabel['href'] for filitedLabel in FilitedLabel]

        for blockLink in BlockLink:
            BlockUrl = "https://sh.lianjia.com" + blockLink
            yield scrapy.Request(response.urljoin(BlockUrl), callback=self.parseBlockPage)

    def parseBlockPage(self, response):

        Soup = BeautifulSoup(response.body, features="html.parser")
        try:
            # 这里的获取到的数据明显是json形式的，所以将其用json解析为字典再获取其中键为totalPage的数据
            PageNum = json.loads(Soup.find("div", {"page-data": re.compile("")})['page-data'])['totalPage']
        except TypeError:
            # 这种异常发生在页面没有房源或只有一页的情况下
            PageNum = 1

        for i in range(1, PageNum+1, 1):
            BlockPageUrl = response.url + "pg{}".format(i)
            yield scrapy.Request(response.urljoin(BlockPageUrl), callback=self.parseBlockWithPgNumPage)

    def parseBlockWithPgNumPage(self, response):

        Soup = BeautifulSoup(response.body, features="html.parser")
        # 将存有其中的所有的房源编码的所有标签提取出来
        FilitedLabel = Soup.find_all("li", {"data-lj_action_housedel_id": re.compile("[0-9]*?")})
        # 再将标签中的房源编码提取出来
        HouseId = [filitedLabel['data-lj_action_housedel_id'] for filitedLabel in FilitedLabel]

        for houseId in HouseId:
            HouseUrl = "https://sh.lianjia.com/ershoufang/" + "/{}.html".format(houseId)
            yield scrapy.Request(response.urljoin(HouseUrl), callback=self.parseHousePage)

    def parseHousePage(self, response):
        Soup = BeautifulSoup(response.body, features='html.parser')

        HouseId = response.url.replace(".html/", "").replace("https://sh.lianjia.com/ershoufang/", "")

        # 提取主表题和副标题
        Title = Soup.find_all("div", class_='title')[0]
        MainTitle = Soup.find("h1")['title'].replace('\n', '')
        SubTitle = Soup.find("div", class_="sub")['title'].replace('\n', '')

        # 提取坐标
        try:
            Coordination = re.findall("resblockPosition:\'([0-9\.,]*?)\'", str(Soup))[0]
        except Exception:
            Coordination = ""

        # 提取总价和单价
        TotalPrice = Soup.find("span", class_='total').get_text()
        UnitPrice = Soup.find("span", class_='unitPriceValue').contents[0]

        # 提取小区名字
        CommunityName = Soup.find("div", class_="communityName").contents[2].get_text()

        # 提取行政区信息和板块信息
        LocationInformation = Soup.select("div.areaName span.info a")
        DistrictWhereHouseIsLocated = LocationInformation[0].get_text()
        BlockWhreHouseIsLocated = LocationInformation[1].get_text()

        # 预先定义好一系列的信息
        HouseStyle = ""
        HouseFloor = ""
        HouseArea = ""
        HouseType = ""
        HouseStructure = ""
        HouseOrientation = ""
        HouseDecoration = ""
        HouseListingTime = ""
        HouseLastSaleTime = ""
        HouseYearOfProperty = ""
        HouseTranscationType = ""
        HousePropertyRight = ""

        # 然后爬取一系列的数据
        BasicInfomation = Soup.select("div.content ul li")
        for basicInfomation in BasicInfomation:
            Label = basicInfomation.get_text().replace('\n', '')[:4]
            if Label == "房屋户型":
                HouseStyle = basicInfomation.contents[1]
            elif Label == "所在楼层":
                HouseFloor = basicInfomation.contents[1]
            elif Label == "建筑面积":
                HouseArea = basicInfomation.contents[1]
            elif Label == "建筑类型" or Label == "别墅类型":
                HouseType = basicInfomation.contents[1]
            elif Label == "房屋朝向":
                HouseOrientation = basicInfomation.contents[1]
            elif Label == "建筑结构":
                HouseStructure = basicInfomation.contents[1]
            elif Label == "装修情况":
                HouseDecoration = basicInfomation.contents[1]
            elif Label == "产权年限":
                HouseYearOfProperty = basicInfomation.contents[1]
            elif Label == "挂牌时间":
                HouseListingTime = basicInfomation.contents[3].get_text()
            elif Label == "上次交易":
                HouseLastSaleTime = basicInfomation.contents[3].get_text()
            elif Label == "交易权属":
                HouseTranscationType = basicInfomation.contents[3].get_text()
            elif Label == "房屋用途":
                HouseUsage = basicInfomation.contents[3].get_text()
            elif Label == "产权所属":
                HousePropertyRight = basicInfomation.contents[3].get_text()
        yield {
            "房源编码": HouseId,
            "主标题": MainTitle,
            "副标题": SubTitle,
            "总价（万元）": TotalPrice,
            "单价（元）": UnitPrice,
            "坐标": Coordination,
            "小区名称": CommunityName,
            "所在行政区": DistrictWhereHouseIsLocated,
            "所在版块": BlockWhreHouseIsLocated,
            "房屋户型": HouseStyle,
            "所在楼层": HouseFloor,
            "建筑面积": HouseArea,
            "建筑类型": HouseType,
            "建筑结构": HouseStructure,
            "房屋朝向": HouseOrientation,
            "装修情况": HouseDecoration,
            "产权年限": HouseYearOfProperty,
            "挂牌时间": HouseListingTime,
            "上次交易": HouseLastSaleTime,
            "交易权属": HouseTranscationType,
            "房屋用途": HouseUsage,
            "产权所属": HousePropertyRight
        }