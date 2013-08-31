#! /usr/bin/python
import urllib
import re

i=10000
while i<10004:
	istr=str(i)
	url="http://www.thingiverse.com/thing:"+istr
	htmlfile=urllib.urlopen(url)
	htmltext=htmlfile.read()
	regex='<div id="description" class="thing-info-content">(.+?)</div>'
	pattern=re.compile(regex, re.S)
	description=re.findall(pattern, htmltext)
	print "thing:", istr, " 's description is: ", description
	myfile=file("description.txt", 'a')
	print>>myfile,"thing:", istr, " 's description is: ", description
	myfile.close()
	i+=1
