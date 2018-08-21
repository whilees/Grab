# -*- coding: utf-8 -*-  
import http.cookiejar
import urllib.request
import urllib.parse
import json
import time
import multiprocessing
import os
import schedule
import base64
import threading
from PIL import Image
import datetime

def getOpener(head):
    # deal with the Cookies
    cj = http.cookiejar.CookieJar()
    pro = urllib.request.HTTPCookieProcessor(cj)
    opener = urllib.request.build_opener(pro)
    header = []
    for key, value in head.items():
        elem = (key, value)
        header.append(elem)
    opener.addheaders = header
    return opener

def getaccess(opener,url):
	html = opener.open(url)
	data = json.loads(html.read())
	#print(data)
	if data['Result'] ==True:
		return data['Data']
	else:
		return False

def CreatePost(post):
	return urllib.parse.urlencode(post).encode()


def postaccess(opener,url,post={}):
	html = opener.open(url,CreatePost(post))
	data = json.loads(html.read())
	print(data)
	if data['Result'] ==True:
		return data['Data']
	else:
		return False

def postaccessjudge(opener,url,post={}):
	html = opener.open(url,CreatePost(post))
	data = json.loads(html.read())
	print(data)
	if data['Result'] ==True:
		return True
	else:
		return False

def check(orderNo):
	url = 'http://twk.qk365.com/WaitAcceptOrder/GetRequireJobPositions'
	postData9 = {
	    'decorationOrderNO': orderNo,
	}
	res = postaccess(opener,url,postData9)
	return res

def judge(no):
	postjudge = {'orderNo': no,}
	judgehtml = 'http://twk.qk365.com/WaitAcceptOrder/AcceptOrderConditionJudge'
	judgeres = postaccessjudge(opener,judgehtml,postjudge)
	return judgeres

def getorderlist():
	url = 'http://twk.qk365.com/WaitAcceptOrder/WaitAcceptOrderQuery'
	postData = {
	    'CurrentPage': '1',
	    'PageSize': '15',
	    'CityNameDistrictName': '',
	}
	res = postaccess(opener,url,postData)
	return res['list']['ItemList']

def getvalide():
	url = 'http://twk.qk365.com/WaitAcceptOrder/GetValidateCode'
	res = getaccess(opener,url)
	if res:
		return res

def savevalideimage(imgDatas):
	if imgDatas['imgDatas']:
		i = 0
		savesrc = ('z:/graborder/'+imgDatas['imgId']+'/')
		os.mkdir(savesrc)
		for img in imgDatas['imgDatas']:
			data = base64.b64decode(img)
			file = open(savesrc+(str(i)+'.jpg'),'wb')
			file.write(data)
			file.close()
			i = i + 1
		return savesrc

def getvalidCodeValue(savesrc):
	value = ''
	for x in range(0,6):
		imgsrc = (savesrc + str(x) + '.jpg')
		res = judgeimage(imgsrc)
		if res:
			value = value + str(x)
	return value

def judgeimage(src):
	i = 1
	j = 1
	img = Image.open(src)#读取系统的内照片
	width = img.size[0]#长度
	height = img.size[1]#宽度
	for i in range(0,width):#遍历所有长度的点
		for j in range(0,height):#遍历所有宽度的点
			data = (img.getpixel((i,j)))#打印该图片的所有点
			# print (data)#打印每个像素点的颜色RGBA的值(r,g,b,alpha)
			# print (data[0])#打印RGBA的r值
			if (data[0]<30):#RGBA的r值大于170，并且g值大于170,并且b值大于170
				return False
	return True

def CreatPostFriendsDict(no):
	frienddict = ''
	time.sleep(4)
	positiondata= CreatRequireFriends(no)
	for postion in positiondata['list']:
		time.sleep(4)
		friend = getCurrFriend(postion['PositionNo'],no)
		frienddict = (frienddict + postion['PositionNo'] + '-' + friend[0]['CustomerAccount'] + ',')
	return frienddict[:-1]
		

def CreatRequireFriends(no):
	postData = {'decorationOrderNO': no}
	url = 'http://twk.qk365.com/WaitAcceptOrder/GetRequireJobPositions'
	res = postaccess(opener,url,postData)
	return res

def getCurrFriend(postion,no):
	postData = {'positionNo': postion, 'decorationOrderNo': no}
	url = 'http://twk.qk365.com/WaitAcceptOrder/GetCurrPositionFriends'
	res = postaccess(opener,url,postData)
	return res

def targetpost(no):
	global validCodeId,validCodeValue,flag
	dic = CreatPostFriendsDict(no)
	time.sleep(5)
	Creatvalid()
	postdata = {
		'orderNo': no,
		'validCodeId': validCodeId,
		'validCodeValue': validCodeValue,
		'workerDict': dic,
		#'workerDict': '9037-15386578898,9038-13730768333,9039-13882779359,9040-18996868266',
	}
	url = ('http://twk.qk365.com/WaitAcceptOrder/AcceptOrder')
	res = postaccessjudge(opener,url,postdata)
	if res:
		flag = False
		print(res)

def lockorder(no):
	postjudge = {'decorationOrderNo': no,'isUse':True}
	judgehtmlx = 'http://twk.qk365.com/WaitAcceptOrder/UpdateAcceptWaitTime'
	islock = postaccessjudge(opener,judgehtmlx,postjudge)
	return islock

def islock(no):
	postjudge = {'orderNo': no}
	judgehtmlx = 'http://twk.qk365.com/WaitAcceptOrder/AcceptOrderConditionJudge'
	islock = postaccessjudge(opener,judgehtmlx,postjudge)
	return islock

def mainpost():
	global flag
	orderlist = getorderlist()
	if orderlist:
		for order in orderlist:
			if (not order['IsDistrictCanAccept'] == 0) and order['RoomCount']>2 and flag:
				isl = islock(order['DecorationOrderNo'])
				if isl:
					lockorder(order['DecorationOrderNo'])
					islocked = islock(order['DecorationOrderNo'])
					if islocked:
						print('grabing'+order['DecorationOrderNo'])
						#flag = False
						targetpost(order['DecorationOrderNo'])
					else:
						print(order['DecorationOrderNo']+'被抢下一个哦')
					
				else:
					print(order['DecorationOrderNo']+'被抢下一个')
	else:
		print('no order')

def main():
	global flag
	i = 0
	time.sleep(57)
	while (flag and i<18):
		mainpost()
		i = i + 1
		time.sleep(0.2)

def Creatvalid():
	global validCodeId,validCodeValue
	validres = getvalide()
	saveres = savevalideimage(validres)
	validCodeId= validres['imgId']
	validCodeValue= getvalidCodeValue(saveres)

def getServerTime():
	url = 'http://twk.qk365.com/WaitAcceptOrder/WaitAcceptOrderQuery'
	postData = {
	    'CurrentPage': '1',
	    'PageSize': '15',
	    'CityNameDistrictName': '',
	}
	res = opener.open(url,CreatePost(postData))
	print(res.info())
	servertime = res.info()['Date']
	return servertime

def UpdateOsTime():
	timeformat(getServerTime())

def timeformat(t):
	GMT_FORMAT =  '%a, %d %b %Y %H:%M:%S GMT'
	timenow = datetime.datetime.strptime(t,GMT_FORMAT)
	timenow = str(timenow)
	hour = str(int(timenow[11:13])+8)
	time = hour+timenow[13:]
	os.system('time {}'.format(time))

def changeflag():
	global flag
	flag = False
	#这个函数来终止有阻塞之嫌
	# global flag
	# time.sleep(40)
	# flag = False


if __name__ == '__main__':
	header = {
	    'Accept': '*/*',
	    'Accept-Encoding': 'gzip, deflate',
	    'Accept-Language': 'zh-CN,zh;q=0.9',
	    'Connection': 'keep-alive',
	    'Cookie': 'UM_distinctid=1636cf8009225e-0d1af51773870a-39614807-1fa400-1636cf800933a8; Hm_lvt_7492c81cf0f836f83a82e76a134d25e2=1526541583; gr_user_id=7bef7a5e-1381-493a-a58e-36168e7e1f6a; _ga=GA1.2.835532017.1526541583; .ECASPXAUTH=UserName=MTU4NTgyMjI3OTU=&Token=KO7y8f5h8crfwtKh/ZTtnTNbruIeKSGWfGTYc17duG1SLr1IEM8jaS6d+WbMdlm4Xaf+/77q1Z2neFwhBDxTvNYbz1WkUz/+2g7u9uUg9PCaMGgRFf/h9WJB5NGoWWcpTR16cmfbT9JLJjLJlNuuNw==; ASP.NET_SessionId=o03ncyun0jbuefmsylqrmkdc',
	    'Host': 'twk.qk365.com',
	    'Referer': 'http://twk.qk365.com/Pages/GetJob.html',
	    'User-Agent': 'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Mobile Safari/537.36',
	    'X-Requested-With': 'XMLHttpRequest',
	}
	#url = 'http://twk.qk365.com/WaitAcceptOrder/GetValidateCode'
	##创建一个opener对象
	opener = getOpener(header)
	print('pending..')
	flag = True
	validCodeId = ''
	validCodeValue = ''
	#加个时间更新
	#UpdateOsTime()
	#time.sleep(4)
	getorderlist()
	#schedule.every().day.at("8:50").do(UpdateOsTime)
	schedule.every().day.at("8:59").do(main)
	#schedule.every().day.at("9:00").do(main)
	#schedule.every().day.at("9:03").do(changeflag)
	#schedule.every().day.at("11:50").do(UpdateOsTime)
	#schedule.every().day.at("12:00").do(main)
	#schedule.every().day.at("12:03").do(changeflag)
	#schedule.every().day.at("14:50").do(UpdateOsTime)
	schedule.every().day.at("14:59").do(main)
	#schedule.every().day.at("15:03").do(changeflag)
	while True:
	    schedule.run_pending()
	    time.sleep(1)