#!/usr/bin/python
#-*- encoding:utf-8 -*-
import sys
import re
import logging
import time
import random
import traceback

import httplib
import urllib,urllib2
import requests
import socket
socket.setdefaulttimeout(5)


from lxml import etree
from bs4 import BeautifulSoup

import algorithm

TEST_FLAG=0

class simpleDoc:
	def __init__(self, doi="", title="", classId=""):
		self._doi = doi
		self._title=title
		self._classid = classId
	def setClassid(self, classid=""):
		self._classid = classid

class OnlineDoc:
	def __init__(self,title="", classId="", sim=0.0, url=""):
		self._title=title
		self._classid = classId
		self._sim = sim
		self._url = url
#params = {'txt_1_sel':'FT$%=|', 'txt_1_value1':'机器学习', 'txt_1_special1':'%', 'currentid':'txt_1_value1', 'dbJson':'coreJson', 'dbPrefix':'SCDB', 'db_opt':'CJFQ,CJFN,CDFD,CMFD,CPFD,IPFD,CCND,CCJD,HBRD,MTRD', 'txt_extension':'','cjfdcode':'', 'expertvalue':'','dbvalue':'','hidTabChange':'','hidDivIDS':'', 'singleDB':'SCDB', 'db_codes':'','singleDBName':'', 'againConfigJson':'false', 'action':'scdbsearch', 'ua':'1.11'}

headers = {
#'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#'Accept-Encoding':'gzip,deflate,sdch',
#'Accept-Language':'zh-CN,zh;q=0.8',
#'Cache-Control':'max-age=0',
#'Connection':'keep-alive',
#'Content-Length':'380',
#'Cookie':'SID_kns=120111; ASP.NET_SessionId=n21i5qa2j5nnkc451ssosi45; RsPerPage=50; CurTop10KeyWord=%2c%u673a%u5668%u5b66%u4e60%2c%u8d44%u672c%u4e3b%u4e49; LID=; ASPSESSIONIDCSSQQTQA=HAKFFBHDDIFGFDEBIFBPKGMP',
#'Host':'epub.cnki.net',
#'Origin':'http://www.cnki.net',
#'Referer':'http://www.cnki.net/',
'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.116 Safari/537.36'
#'Content-Type':'application/x-www-form-urlencoded'
}

#考虑没有搜索结果，或者没有分类标号的结果

def extractWFClasscode(docurl):
	try:
		#req = urllib2.Request(docurl, headers=headers)
		#doc = urllib.urlopen(req).read()
		r = requests.get(docurl, headers=headers, timeout=5)
		doc = r.text
		if TEST_FLAG:
			print "html type: ",type(doc)
		soup = BeautifulSoup(doc,"lxml")
		res = soup.find(text=re.compile(ur"分类号"))
		if not res:
			if TEST_FLAG:
				print ur"分类号没有找到"
			return -1
		if TEST_FLAG:
			print ur"分类号找到"
		classcode=res.parent.parent.nextSibling.nextSibling
		#classcode = classcode.strip()
		classtext=classcode.text.strip()
		if TEST_FLAG:
			print ur"classcode成功得到"
		if len(classtext)<2:
			if TEST_FLAG:
				print ur"分类号长度<2"
				print "classnode type=",type(classcode)
			return -1
		if TEST_FLAG:
			print "classnode type=",type(classcode)
			print "classnode success."
		return classtext
	except Exception, e:
		print ur"万方中没有找到相关文献:" + unicode(e)
		return -1
	return -1

def extractCNKIClasscode(docurl):
	try:
		#req = urllib2.Request(docurl, headers=headers)
		#doc = urllib.urlopen(req).read()
		r = requests.get(docurl, headers=headers, timeout=5)
		doc = r.text
		soup = BeautifulSoup(doc, "lxml")
		#chunks = soup.find_all("div", {"class":"xx_font", "style":"text-align:left;"})
		#assert len(chunks)==1
		res = soup.find(text=re.compile(ur"分类号"))
		if not res:
			return -1
		classcode=res.parent.parent.nextSibling
		classcode=classcode.strip()
		if len(classcode)<2:
			return -1
		return classcode
	except Exception, e:
		print ur"CNKI中没有找到相关文献：" + e
		return -1
	return -1

def getWFClassBytitle(title):
	adoc=simpleDoc(title=title)
	return getWFClass(adoc)

def getCNKIClassBytitle(title):
	adoc=simpleDoc(title=title)
	return getCNKIClass(adoc)

def getWFClass(doc): #返回[(doctitle, url,sim, 类别),()]列表
	lst=[]
	#base_url="http://search.cnki.com.cn/search.aspx?q="
	base_url = "http://s.wanfangdata.com.cn/Paper.aspx?q="
	url = base_url + urllib.quote(doc._title.encode("utf-8"))	
	title_len= len(doc._title)
	max_doc=OnlineDoc()
	max_score = 0.0
	final_code=""
	if TEST_FLAG:
		print "get into getWFClass."
	try:
		req = urllib2.Request(url, headers=headers)
		search_result = urllib2.urlopen(req, timeout=5).read()
		if TEST_FLAG:
			print "urlopen success."
		soup = BeautifulSoup(search_result, "lxml")
		if TEST_FLAG:
			print "build soup success"
		links = soup.find_all("li", class_="title_li")
		#if not links: #没有搜索结果
		#	return []
		for chunk in links:
			link = chunk.find_all("a")[2]
			if not link:
				pass
			if TEST_FLAG:
				print link
				print type(link.text)
			titl = link.text
			#sim = algorithm.LCS(doc._title, titl)*1.0/title_len
			sim = algorithm.lcs_sim(doc._title, titl)
			if sim<0.7:
				continue
			url = link.attrs['href']
			if TEST_FLAG:
				print "wanfang before extractWFClasscode success"
			class_code = extractWFClasscode(url)
			lst.append((titl, url, sim, class_code))
			if sim>max_score:
				max_doc = OnlineDoc(titl, class_code, sim, url) 
				max_score = sim
			final_code += class_code
			final_code += ";"
			#outline= u"---万方---:" + titl + "\t" + class_code + "\t" + str(sim) + "\t" + url
			#logging.debug(outline)
			if TEST_FLAG:
				print "wanfang fout.write success."
	except Exception, e:
		print e
	return [max_doc._title, max_doc._classid, max_doc._sim, max_doc._url ]
	
def getCNKIClass(doc):
	lst=[]
	base_url="http://search.cnki.com.cn/search.aspx?q="
	url = base_url + urllib.quote(doc._title.encode("utf-8"))	
	title_len= len(doc._title)
	final_code=""
	max_doc=OnlineDoc()
	max_score = 0.0
	try:
		req = urllib2.Request(url, headers=headers)
		search_result = urllib2.urlopen(req, timeout=5).read()
		soup = BeautifulSoup(search_result, "xml")
		links = soup.find_all("div", class_="wz_content")
		#if not links: #没有搜索结果
		#	return []
		for chunk in links:
			link = chunk.find("a")
			titl = link.text
			#sim = algorithm.LCS(doc._title, titl)*1.0/title_len
			sim = algorithm.lcs_sim(doc._title, titl)
			if sim<0.7:
				continue
			url = link.attrs['href']
			class_code = extractCNKIClasscode(url)
			lst.append((titl, url, sim, class_code))
			if sim>max_score:
				max_doc = OnlineDoc(titl, class_code, sim, url) 
				max_score = sim
			final_code += class_code
			final_code += ";"
	except Exception, e:
		print e
	#return max_doc 
	return [max_doc._title, max_doc._classid, max_doc._sim, max_doc._url ]

def readIntoDocpoolfromPaperlist(paperlist):
	fin = open(paperlist, 'r')
	for line in fin:
		lines = line.strip().decode("utf-8").split("\3")
		doi = lines[0]
		title = lines[1]
		class_label = ";".join(lines[2:])
		asdoc = simpleDoc(doi=doi, title=title, classId=class_label)
		doc_pool.append(asdoc)

def readIntoDocpool(xmlfilename):
	tree = etree.parse(xmlfilename)
	root = tree.getroot()
	gene=root.findall(".//doi")
	testNo=0
	for adoi in gene:
		doi=adoi.text.strip()
		adoc = adoi.getparent()
		papr = adoi.find("../paprtitl")
		asdoc=simpleDoc(doi=doi, title=papr.text.strip())
		if 1 or testNo<1:
			doc_pool.append(asdoc)
		testNo += 1
