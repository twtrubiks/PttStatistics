# coding=UTF-8
import time
import requests
import sys
import jieba
import operator
from datetime import datetime
from bs4 import BeautifulSoup
requests.packages.urllib3.disable_warnings()
#可自行加入新的詞進去,增加斷詞精準度
jieba.load_userdict("dictNew.txt")
rs = requests.session()

def over18(board):
    res = rs.get('https://www.ptt.cc/bbs/' + board + '/index.html', verify = False)
    #先檢查網址是否包含'over18'字串 ,如有則為18禁網站
    if ( res.url.find('over18') > -1 ):
       print u"18禁網頁"
       load = {
           'from':'/bbs/'+board+'/index.html',
           'yes':'yes' 
       }
       res = rs.post('https://www.ptt.cc/ask/over18',verify = False, data = load)
       return  BeautifulSoup(res.text,'html.parser')  
    return BeautifulSoup(res.text,'html.parser') 

def getPageNumber(content) :
    startIndex = content.find('index')
    endIndex = content.find('.html')
    pageNumber = content[startIndex+5 : endIndex]
    return pageNumber

def title_count(PttName, ParsingPage, ALLpage):
    Titlesplit = ""
    count = 0 

    for index in range(ALLpage, ALLpage - int(ParsingPage), -1): 
        count += 1
        #避免被認為攻擊網站 
        time.sleep(0.1)
        url = 'https://www.ptt.cc/bbs/'+ PttName +'/index'+ str(index) +'.html'
        res = rs.get(url, verify = False)
        soup = BeautifulSoup(res.text,'html.parser')

        if (soup.title.text.find('Service Temporarily') > -1) :
            print 'Service Temporarily', soup.title.text

        for r_ent in soup.find_all( class_="r-ent"):
            link = r_ent.find('a') 
	    if ( link != None ):              
               title = link.text
               try:
                   Titlesplit += title.split(']')[1].strip()
               except:
                   Titlesplit += title.strip()
        print u"等稍等: " + str(100 * count / ParsingPage ) + " %."

    return jieba.cut(Titlesplit)

def push_count(PttName, ParsingPage, ALLpage):
    UrlPer = []
    pushcontent = ""
    count = 0

    #先抓取每篇文章的URL
    for index in range(ALLpage, ALLpage - int(ParsingPage), -1): 
        #避免被認為攻擊網站
        time.sleep(0.1)
        url = 'https://www.ptt.cc/bbs/'+ PttName +'/index'+ str(index) +'.html'
        res = rs.get(url, verify = False)
        soup = BeautifulSoup(res.text,'html.parser')

        if (soup.title.text.find('Service Temporarily') > -1) :
            print 'Service Temporarily', soup.title.text

        for r_ent in soup.find_all( class_="r-ent"):
            link = r_ent.find('a') 
	    if ( link != None ):             
               UrlPer.append('https://www.ptt.cc' + link['href'] )   
           
    total = len(UrlPer)  

    #開始抓取每篇文章內容的推文
    while UrlPer :
       time.sleep(0.1)   
       url = UrlPer.pop(0)
       res = rs.get( url,verify = False)
       soup = BeautifulSoup(res.text, 'html.parser')
       if ( soup.title.text.find('Service Temporarily') > -1 ) :
          UrlPer.append( url )
          #print 'error_URL:',url
          time.sleep(1)   
       else :     
          count += 1
          #print 'OK_URL:', url       
          for push in soup.select('.push-content') :
              pushcontent += push.text[1:]
          print u"等稍等: " + str(100 * count / total ) + " %."

    return  jieba.cut(pushcontent)                 

# pyhton PttStatistics.py [統計型態] [板名] [爬取頁數]
# python PttStatistics.py title gossiping 10
if __name__ == "__main__":
    search, PttName, ParsingPage = str(sys.argv[1]), str(sys.argv[2]) , int(sys.argv[3])
    print 'Start parsing ' + PttName + '....'
    fileName = '-'+ PttName + '-' + datetime.now().strftime('%Y%m%d%H%M%S') + '.txt'
    start_time = time.time()
    soup = over18(PttName) 
    ALLpageURL = soup.select('.btn.wide')[1]['href']
    ALLpage = int(getPageNumber(ALLpageURL)) + 1
    #print 'Total pages:',ALLpage
    print 'Start parsing ' + search + ' count....'
    fileName = search + fileName
    
    if( search!='title' and search != 'push' ) :
        print u"ERROR !! 請輸入 title or push !!"
        sys.exit()
    if( search == 'title'):
        dataList = title_count(PttName, ParsingPage, ALLpage )
    if( search == 'push'):
        dataList = push_count(PttName, ParsingPage, ALLpage)


    print u"字詞統計中,請稍等......"

    dic = {}
  
    #字詞統計
    for ele in dataList :
        if ele not in dic:
           dic[ele] = 1
        else:
           dic[ele] = dic[ele] + 1       

    sorted_word = sorted(dic.items(), key = operator.itemgetter(1), reverse = True)    

    line = ''
    for ele in sorted_word:
        if( len(ele[0]) > 1 ): #只顯示一個字以上的詞，如需顯示一個字的詞請註解掉此行
           line += ele[0] + ' ' + str(ele[1]) + '\n'

    with open(fileName,'a') as f:
         f.write( line.encode('utf8') )   

          
    print u'====================完成===================='
    print u'execution time:' + str(time.time() - start_time)+'s'
    
