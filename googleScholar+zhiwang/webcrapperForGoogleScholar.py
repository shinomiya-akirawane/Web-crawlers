import csv
from time import sleep
import requests
import json
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import difflib
from urllib.parse import quote
from scraper_api import ScraperAPIClient
from langSpilt import Split
import Configs
@staticmethod
class Duplications:
    def duplicateEnglishPaperSearch(index):
        url = "https://www-webofscience-com.libproxy.ucl.ac.uk/wos/woscc/basic-search"
        page = webdriver.Chrome()
        page.get(url)
        sleep(4)
        login(page)
        sleep(4)
        if page.find_element_by_id('onetrust-accept-btn-handler').is_displayed():
            page.find_element_by_id('onetrust-accept-btn-handler').click()
        if page.find_element_by_name('search-main-box').is_displayed():
            page.find_element_by_name('search-main-box').send_keys(index)
        else:
            sleep(2)
            page.find_element_by_name('search-main-box').send_keys(index)
        if page.find_element_by_id('pendo-close-guide-ecbac349').is_displayed():
            page.find_element_by_id('pendo-close-guide-ecbac349').click()
        page.find_element_by_css_selector('[type="submit"]').click()
        sleep(2)
        currentUrl = page.current_url
        #when there is no result, the url of page will not change
        if currentUrl == url:
            paperInfoDict = {
                'title':'',
                'match':'n',
                'journal':'',
                'lang' :'en',
                'date':'',
                'cite':'',
            }
            return paperInfoDict
        content = page.page_source.encode('utf-8')
        response = BeautifulSoup(content, 'lxml')
        targetTerm = findTargetTerm(response,index)
        paperTitle = targetTerm.select_one('[data-ta="summary-record-title-link"]').text
        paperJournal = targetTerm.select_one('[cdxanalyticscategory="wos-recordCard_Journal_Info"]')
        paperJournal = 'none' if paperJournal == None else paperJournal.text
        paperDate = targetTerm.select_one('[name="pubdate"]')
        paperDate = 'none' if paperDate == None else paperDate.text
        paperDate = paperDate.replace('|','') if '|' in paperDate else paperDate
        paperCite = targetTerm.select_one('[cdxanalyticscategory="wos-recordCard_Citations"]')
        paperCite = '0' if paperCite == None else paperCite.text
        paperInfoDict = {
                'title':paperTitle,
                'journal':paperJournal,
                'lang' :'en',
                'date':paperDate,
                'cite':paperCite,
            }
        if difflib.SequenceMatcher(None, paperTitle.lower(), index.lower()).quick_ratio() > 0.90:
            paperInfoDict['match'] = 'y'
        else:
            paperInfoDict['match'] = 'n'
        page.close()
        return paperInfoDict

    def getPaperJournal(targetTerm):
        journal =  targetTerm.select('[class="source"]')
        journal = journal[0].find_all('a')[0].text
        return journal

    def getPaperDate(targetTerm):
        date =  targetTerm.select('[class="date"]')
        date = date[0].text
        return date

    def getPaperCite(targetTerm):
        cite =  targetTerm.select('[class="quote"]')
        if cite[0].text == '\n':
            cite = '0'
        else:
            cite = cite[0].find_all('a')[0].text
        return cite
    def duplicateChinesePapaerSearch(index):
        url = "https://www.cnki.net/"
        chrome_options=Options()
        chrome_options.add_argument('--headless')
        page = webdriver.Chrome(chrome_options=chrome_options)
        page.get(url)
        page.find_element_by_css_selector('#txt_SearchText').send_keys(index)
        page.find_element_by_css_selector('body > div.wrapper.section1 > div.searchmain > div > div.input-box > input.search-btn').click()
        content = page.page_source.encode('utf-8')
        response = BeautifulSoup(content, 'lxml')

        #get all terms 
        allTerms = response.find_all('tbody')
        if allTerms == []:
            paperInfoDict = {
                'title':'',
                'match':'n',
                'journal':'',
                'lang' :'zh',
                'date':'',
                'cite':'',}
            return paperInfoDict
        allTerms = allTerms[0].contents
        #get the result title and the result term
        paperTitle,targetTerm = getPaperTitle(allTerms,index)
        paperJournal = getPaperJournal(targetTerm)
        paperLang = checkIndexType(index)
        paperDate = getPaperDate(targetTerm)
        paperCite = getPaperCite(targetTerm)
        paperInfoDict = {
            'title':paperTitle,
            'journal':paperJournal,
            'date':paperDate,
            'cite':paperCite,
            'lang':paperLang
        }
        if difflib.SequenceMatcher(None, paperTitle, index).quick_ratio() > 0.90:
            paperInfoDict['match'] = 'y'
        else:
            paperInfoDict['match'] = 'n'
        page.close()
        return paperInfoDict

    def getPaperTitle(allTerms,index):
        paperTitle = 'origin'
        for term in allTerms:
            title = term.select('[class="fz14"]')
            title = title[0].text
            if title == index:
                paperTitle = title
                targetTerm = term
                return paperTitle,targetTerm
        if paperTitle == 'origin':
            paperTitle = allTerms[0]
            paperTitle = paperTitle.select('[class="fz14"]')
            paperTitle = paperTitle[0].text
            targetTerm = allTerms[0]
            return paperTitle,targetTerm

    def checkIndexType(title):
        checkUrl = "https://fanyi.baidu.com/langdetect"
        data = {'query':title}
        headers = {
        'User-agent':
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582"
        }
        response = requests.post(checkUrl,data=data,headers = headers)
        resultJson = response.content.decode()
        result = json.loads(resultJson)['lan']
        return result

def extractTitle(line):
    return line[4]

def login(page):
    #fill your own username and password
    page.find_element_by_id('username').send_keys('')
    page.find_element_by_id('password').send_keys('')
    page.find_element_by_name('_eventId_proceed').click()

def findTargetTerm(allTerms,index):
    resultList = allTerms.select('[class = "gs_ri"]')
    for result in resultList:
        title = result.find('h3').text
        if title == index:
            return result
    return resultList[0]

def extractEngInfo(string):
    journal = []
    if re.search(r'\d+', string) != None:
        year = int(re.search(r'\d+', string).group())
    else:
        year = 'no'
    date = str(year)
    string = string.split('-')
    for s in string:
        if ',' in s and ('1' in s or '2' in s):
            string = s.split(',')
            break
    journal = string[0].replace(u'\xa0','')
    infoDict = {
        'journal':journal,
        'date':date
    } 
    return infoDict

def completeJournal(title):
    url = "https://www.mybib.com/api/autocite/search"
    headers = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
    }
    titleEncoded = quote(title) 
    params = {
        'q':titleEncoded,
        'sourceId':'article_journal'
            }
    response = requests.get(url,headers=headers,params=params).text
    if response == 'Bad Request':
        result = 'noCompleted'
        return result
    response = json.loads(response)
    result = response['results'][0]['metadata']['containerTitle']
    return result

def englishPaperSearch(index):
    client = ScraperAPIClient('a98ab53a9eb969480922e56c9787c8f6')
    url = "https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q=" + index.replace(' ','+')
    content = client.get(url)
    response = BeautifulSoup(content.content,'lxml')
    if response.select('[id = "gs_res_ccl_mid"]') != []:
        allTerms = response.select('[id = "gs_res_ccl_mid"]')[0]
    else:
        paperInfoDict = {
            'match':'n',
            'title':'',
            'journal':'',
            'lang' :'en',
            'date':'',
            'cite':'',
        }
        return paperInfoDict
    if allTerms.text == '':
        paperInfoDict = {
            'title':'',
            'match':'n',
            'journal':'',
            'lang' :'en',
            'date':'',
            'cite':'',
        }
        return paperInfoDict
    targetTerm = findTargetTerm(allTerms,index)
    paperTitle = targetTerm.find('h3').contents
    for c in paperTitle:
        if c.name == 'a':
            paperTitle = c.text
        elif difflib.SequenceMatcher(None, c.text.lower(), index.lower()).quick_ratio() > 0.90:
            paperTitle = c.text
    if isinstance(paperTitle, list):
        paperInfoDict = {
            'match':'n',
            'title':'',
            'journal':'',
            'lang' :'en',
            'date':'',
            'cite':'',
        }
        return paperInfoDict
    paperInfo = targetTerm.select_one('[class="gs_a"]').text
    infoDict = extractEngInfo(paperInfo)
    paperJournal = infoDict['journal']
    if '…' in paperJournal:
        paperJournal = completeJournal(paperTitle)
    if paperJournal == 'noCompleted':
        paperJournal += infoDict['journal']
    paperDate = infoDict['date']
    paperCite = targetTerm.select_one('[class = "gs_fl"]')
    if 'Cited by' in paperCite.text:
        for content in paperCite.contents:
            if 'Cited by' in content.text:
                paperCite = content.text.replace('Cited by','')
    else:
        paperCite = '0'
    paperInfoDict = {
            'title':paperTitle,
            'journal':paperJournal,
            'lang' :'en',
            'date':paperDate,
            'cite':paperCite,
        }
    if difflib.SequenceMatcher(None, paperTitle.lower(), index.lower()).quick_ratio() > 0.95:
        paperInfoDict['match'] = 'y'
    else:
        paperInfoDict['match'] = 'n'
    return paperInfoDict

def englishCrapper():
    with open('en.csv','r',encoding='utf-8') as papers:
    #for loop deal with each fruit
        fruitList = csv.reader(papers)
        cnt=0
        for fruit in fruitList:
            if fruit == []:
                continue
            #get the fruit title as search index to search
            searchIndex = extractTitle(fruit)
            prjno = fruit[0]
            #judge the index type
            paperResultDict = englishPaperSearch(searchIndex)
            line = prjno + ',' + str(cnt) + ',' +searchIndex+ ',' + paperResultDict['match'] + ',' + paperResultDict['lang'] + ',' + paperResultDict['journal']+ ',' + paperResultDict['cite']+ ',' + paperResultDict['date']+ ',' + paperResultDict['title'] + '\r\n'
            with open(Configs.crawlerResultPath,'a',encoding = 'utf-8') as enpapers:
                enpapers.write(line)
            cnt+=1
            print (prjno)

def main():
    Split.spilt()
    englishCrapper()

if __name__ == '__main__':
    main()