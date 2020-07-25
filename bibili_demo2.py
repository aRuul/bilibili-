import urllib3
import urllib.request
import sys
import re
import json
import requests
import gzip
import time
import xlwt
import sqlite3
from io import BytesIO
from bs4 import BeautifulSoup
url="https://www.bilibili.com/ranking"                                                #要爬取的b站排行榜链接

#正则表达式
findrank=re.compile(r'<div class="num">(.*?)</div>')                                            #排名
findav=re.compile(r'<li class="rank-item" data-id="(.*?)" data-rank="[0-9]+">')                 #av号
findtitle=re.compile(r'<img alt="(.*?)" src=[\s\S]*?',re.S)                                     #标题
findplaynum=re.compile(r'<span class="data-box"><i class="b-icon play"></i>(.*?)</span>')       #播放量
finddanmu=re.compile(r'<span class="data-box"><i class="b-icon view"></i>(.*?)</span>')         #弹幕量
findupname=re.compile(r'<span class="data-box"><i class="b-icon author"></i>(.*?)</span>')      #up主
findscore=re.compile(r'<div class="pts"><div>(.*?)</div>综合得分')                              #综合评分
findchannel=re.compile(r'<span class="channel-name">(.*)</span>')                               #频道分区

dbpath='bilibili.db'
savepath='bilibili.xls'

#t通过av号/aid爬取下载链接的函数
def download_vedio(aid):
    cid_api="https://www.bilibili.com/widget/getPageList?aid="+aid       #通过aid/av号获得cid的接口
    headerss={
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36 Edg/84.0.522.40",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        }
    r=requests.get(cid_api,headers=headerss)
    cid_data=json.loads(r.text)
    cid=str(cid_data[0]['cid'])                                          #获得cid

    download_url="https://www.xbeibeix.com/api/bilibiliapi.php?aid="+aid+"&cid="+cid       #下载接口
    rr=requests.get(download_url,headers=headerss)
    download_data=json.loads(rr.text)
    download=download_data['url']
    return download

#频道分区
def channell(av):                                      #不能命名成channel，否则python以为你没声明，会报错
    vedio_url="https://www.bilibili.com/video/av"+av   #视频链接 以av号的链接形式访问，减少爬取所用开销
    headers={
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.61",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    }
    req=urllib.request.Request(url=vedio_url,headers=headers)
    #html="null"
    try:
        response=urllib.request.urlopen(req)
        #解决b站采取gzip压缩的方法
        html=response.read()
        buff=BytesIO(html)
        f=gzip.GzipFile(fileobj=buff)
        html=f.read().decode('utf-8')
        #html=response.read().decode('utf-8')
        #print(html)
    except urllib.error.URLError as e:
        if hasattr(e,"code"):
            print(e.code)
        if hasattr(e,"reason"):
            print(e.reason)
    #靓汤解析数据
    soup=BeautifulSoup(html,"html.parser")
    #找需要的标签内容
    for item in soup.find_all('div',id="app"):
        #print(item)
        item=str(item)

        #频道分区
        channel=re.findall(findchannel,item)
        if len(channel):
            return channel[0]
        else:
            return " "
    #return channel


#获取内容
def askURL(url):
    headersss={
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.61",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
    }
    req=urllib.request.Request(url=url,headers=headersss)
    #html="null"
    try:
        response=urllib.request.urlopen(req)
        html=response.read().decode('utf-8')
        #print(html)
    except urllib.error.URLError as e:
        if hasattr(e,"code"):
            print(e.code)
        if hasattr(e,"reason"):
            print(e.reason)
    return html

#解析网页
def getInform():
    datalist=[]
    html=askURL(url)
    #靓汤解析数据
    soup=BeautifulSoup(html,"html.parser")
    #找需要的标签内容
    count=0
    for item in soup.find_all('li',class_="rank-item"):
        count=count+1
        #print(item)
        data=[]
        item=str(item)

        #排名
        rank=re.findall(findrank,item)[0]
        data.append(rank)

        #标题
        title=re.findall(findtitle,item)
        if len(title):
            titlee=title[0]
        else:
            titlee=' '
        data.append(titlee)
        #data.append(img)


        #播放量
        playnum=re.findall(findplaynum,item)[0]
        data.append(playnum)

        #弹幕量
        danmu=re.findall(finddanmu,item)[0]
        data.append(danmu)

        #up主
        upname=re.findall(findupname,item)[0]
        data.append(upname)

        #综合评分
        score=re.findall(findscore,item)[0]
        data.append(score)

        #av号(作为中间数据)
        av=re.findall(findav,item)[0]
        avv=str(av)                                                             #av号转成string类型
        #print(avv)
        #time.sleep(1)
        #爬取视频分区
        channel=channell(avv)                                                   #调用channell函数，不能命名成channel，否则python以为你没声明，会报错
        data.append(channel)

        #通过av号获取封面
        fm_api="https://api.bilibili.com/x/web-interface/view?aid=%s"%(avv)     #b站视频封面的api,aid= 后接av号

        #header信息要设置成chrome浏览器的，Edge会失败，不知道为啥，很迷
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36',
                   'Referer': 'https://www.bilibili.com'}

        urllib3.disable_warnings()   #去掉警告
        response = requests.get(fm_api, headers=headers, verify=False)          #证书验证设为FALSE

        content = json.loads(response.text)
        statue_code = content.get('code')
        if statue_code == 0:
            fm=content.get('data').get('pic')                                   #获得封面的网址
            data.append(fm)
            #data.append(fm.split())                                             #fm.split() 把str强制转换成list
            #print(content.get('data').get('pic'))
        else:
            print('啊嘞？出错了！')

        #通过av号得到视频链接
        vedio_link="https://www.bilibili.com/video/av"+avv
        data.append(vedio_link)
        #data.append(vedio_link.split())                                        #强制转换成list

        #通过av号获得获得下载链接
        download_url=download_vedio(avv)
        #download_url=download_urll.replace(" ","")
        #data.append(download_url.split())                                      #download_url.split() 把str强制转换成list
        data.append(download_url)
        datalist.append(data)                                                  #把所有信息放到datalist中
        time.sleep(2)                                                          #防止测试程序的时候ip被封，每次完成一次休息1s
        print("这是第",count,"条，给爷快点爬...")
        print(data)
        #print(datalist)
    #print(datalist)
    return datalist
                                                       

#保存到excel
def savedata(datalist,savepath):
    book=xlwt.Workbook(encoding="utf-8",style_compression=0)
    sheet=book.add_sheet('bilibili_rank',cell_overwrite_ok=True)
    col=("排名","标题","播放量","弹幕量","up主","综合评分","分区","封面","视频链接","下载链接") #设定列名
    for i in range(0,10):
        sheet.write(0,i,col[i])
    for i in range(0,100):
        print("这是第",i+1,"条")
        data=datalist[i]
        for j in range(0,10):
            sheet.write(i+1,j,data[j])
    book.save('bilibili.xls')  #保存


#创建基本数据库
def create_db(dbpath):
    connect=sqlite3.connect(dbpath)    #建立并连接数据库
    c=connect.cursor()   #获取游标
    sql='''
       create table bilibili_data(
       rank integer primary key,
       title varchar,
       bfl varchar,
       dml varchar,
       up varchar,
       score int,
       channel varchar,
       fm_link text,
       vedio_link text,
       download text
       )
    '''
    c.execute(sql)   #执行sql语句
    connect.commit() #提交数据库
    connect.close()  #关闭数据库
    #print("")

#保存数据库
def savedb(datalist,dbpath):
    create_db(dbpath)
    connect=sqlite3.connect(dbpath)    #建立并连接数据库
    c=connect.cursor()   #获取游标
    for data in datalist:
        for index in range(len(data)):
            if index==0 or index==5:
            #if index==5:
                continue
            data[index]='"'+str(data[index])+'"'   #data[index]是list，应该强制转换成string类型
        sql='''
              insert into bilibili_data(
              rank,title,bfl,dml,up,score,channel,fm_link,vedio_link,download)
              values(%s)'''%",".join(data)
        print(sql)
        c.execute(sql)
        connect.commit()
    c.close()
    connect.close()
    print()


#main函数
if __name__=="__main__": 
    #askURL(url)
    datalist=getInform()
    #savedata(datalist,savepath)
    savedb(datalist,dbpath)

