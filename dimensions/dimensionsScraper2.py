
from selenium import webdriver
from time import sleep
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions
import re
import csv
import pypinyin
import Configs
import preprocessFile
def extractInfo(labels) -> dict:
    infoDict = {}  
    for label in labels:
        text = label['aria-label']
        info = text.split(',',2)[2].split('.',2)[0]
        if ' ' in info:
            info = info.replace(' ','')
        if ',' in info:
            info = info.replace(',','')
        year = text.split(',',2)[1]
        if ' ' in year:
            year = year.replace(' ','')
        infoDict[year] = info
    return infoDict

def extractInfo2(infoList) -> list:
    resList = []
    if infoList == []:
        return []
    for content in infoList.contents:
        researchField = content.find('div',attrs =  {'class' : re.compile("textcrop")}).text
        if ' ' in researchField:
            researchField = researchField.replace(' ','')
        if ',' in researchField:
            researchField = researchField.replace(',','.')
        resList.append(researchField)
    return resList
def extractProjectNums(projectNums:list) -> str:
    searchText = ''
    for projectNum in projectNums:
        searchText += ' '+str(projectNum)+' OR'
    searchText = searchText.rstrip('OR')
    searchText = searchText.strip()
    return searchText

def getResearchersPage(projectNums:list) -> webdriver:
    searchText = extractProjectNums(projectNums)
    url = "https://app.dimensions.ai/analytics/publication/author/aggregated?search_mode=content&search_text="+searchText+"&search_type=kws&search_field=full_search"
    driver = webdriver.Chrome()
    driver.implicitly_wait(60)
    driver.set_window_size(1000,300000)
    driver.get(url)
    return driver

def scrollList(searchPage:webdriver):
    scrollPageJs = 'window.scrollBy(0,300)'
    searchPage.execute_script(scrollPageJs)
    scrollListJs = 'document.getElementById("analytics_infinite_scroll_container").scrollTop=300000'
    searchPage.execute_script(scrollListJs)

def loadAllResearcher(searchPage:webdriver):
    preReseacherListLen = -1
    while True:
        scrollList(searchPage)
        sleep(2)
        researcherList = searchPage.find_elements(By.CSS_SELECTOR,'div[data-bt=list-row]')
        if len(researcherList) == preReseacherListLen:
            break
        else:
            preReseacherListLen = len(researcherList)

def findResearcherName(searchPage:webdriver,names) -> bool:
    wait = WebDriverWait(searchPage,timeout=10,poll_frequency=0.5)
    wait.until(expected_conditions.element_to_be_clickable(("xpath",'//*[@id="onetrust-accept-btn-handler"]')))
    try:
        searchPage.find_element(By.XPATH,'//*[@id="onetrust-accept-btn-handler"]').click()
    except:
        sleep(3)
        searchPage.find_element(By.XPATH,'//*[@id="onetrust-accept-btn-handler"]').click()
    finally:
        page = BeautifulSoup(searchPage.page_source,'lxml')
        researcherDivs = page.find_all('div',attrs =  {'data-bt' : 'list-row'})
        for i in range(0,len(researcherDivs)):
            researcherName = researcherDivs[i].find('a').text
            if researcherName in names:
                try:
                    searchPage.find_element(By.XPATH,'//*[@id="analytics_infinite_scroll_container"]/div[2]/div[2]/div[2]/div[2]/div['+str(i+1)+']/div/div[1]/div[1]/div/a').click()
                except:
                    sleep(3)
                    searchPage.find_element(By.XPATH,'//*[@id="analytics_infinite_scroll_container"]/div[2]/div[2]/div[2]/div[2]/div['+str(i+1)+']/div/div[1]/div[1]/div/a').click()
                finally:
                    return True
        return False

def enterResearcherPage(searchPage:webdriver):
    wait = WebDriverWait(searchPage,timeout=20,poll_frequency=0.5)
    wait.until(expected_conditions.element_to_be_clickable(("xpath",'//*[@id="mainContentBlock"]/div/div/div/div[1]/header/div[2]/div[2]/a')))
    sleep(1)
    try:
        searchPage.find_element(By.XPATH,'//*[@id="mainContentBlock"]/div/div/div/div[1]/header/div[2]/div[2]/a').click()
    except:
        searchPage.save_screenshot('error.png')
def scrapeInfo(driver,name,projectNum) -> dict:
    wait = WebDriverWait(driver,timeout=60,poll_frequency=0.5)
    wait.until(expected_conditions.visibility_of_element_located(('xpath','//*[@id="mainContentBlock"]/div/article[1]/div/section[2]/div/ol')) and expected_conditions.visibility_of_element_located(('xpath','//*[@id="mainContentBlock"]/div/article[1]/div/section[1]/div/ol')) 
    and expected_conditions.visibility_of_element_located(('xpath','.//div[@class = "highcharts-container "]')))
    sleep(5)
    pageContent = BeautifulSoup(driver.page_source,'lxml')
    url = driver.current_url
    driver.close()
    publicationLabels = pageContent.find_all('rect',attrs =  {'aria-label' : re.compile("Publications")})
    publicationDict = extractInfo(publicationLabels)
    citationLabels = pageContent.find_all('path',attrs =  {'aria-label' : re.compile("Citations")})
    citationDict = extractInfo(citationLabels)
    grantLabels = pageContent.find_all('rect',attrs =  {'aria-label' : re.compile("Active grants")})
    grantDict = extractInfo(grantLabels)
    olList = pageContent.find_all('ol',attrs =  {'class' : 'showmore__list'})
    conceptsList = []
    researchFieldList = []
    for i in range(0,len(olList)):
        if i == 0:
            researchFieldList = olList[i]
        elif i == 1:
            conceptsList = olList[i]
    researchFields = extractInfo2(researchFieldList)
    concepts = extractInfo2(conceptsList)
    h3 = pageContent.find("h3",string="Education")
    if h3 != None:
        educations = []
        educationList = h3.next_sibling
        for education in educationList.contents:
            educationItem = education.text
            if ',' in educationItem:
                educationItem = educationItem.replace(',','.')
            educations.append(educationItem)
    else:
        educations = []
    resDict = {
        'projectNum':projectNum,
        'name':name,
        'publicationDict': publicationDict,
        'citationDict': citationDict,
        'grantDict' : grantDict,
        'researchFields': researchFields,
        'concepts': concepts,
        'educations':educations,
        'match':'y',
        'url':url
    }
    return resDict

def search(projectNums:list,names:list) -> dict:
    searchPage = getResearchersPage(projectNums)
    sleep(5)
    loadAllResearcher(searchPage)
    inList = findResearcherName(searchPage,names)
    if inList == True:
        enterResearcherPage(searchPage)
        return scrapeInfo(searchPage,names[0],projectNums[0])
    else:
        blankDict = {
        'projectNum':projectNums[0],
        'name':names[0],
        'publicationDict': {},
        'citationDict': {},
        'grantDict' : {},
        'researchFields': [],
        'concepts': [],
        'educations':[],
        'match': 'n',
        'url': ''
    }
    return blankDict

def extractMing(mings:list):
    if len(mings) == 1:
        pinyinMing = []
        for letter in mings[0]:
            pinyinMing.append([letter])
    elif len(mings) == 2:
        pinyinMing = []
        for letter1 in mings[0]:
            for letter2 in mings[1]:
                pinyinMing.append([letter1,letter2])
    return pinyinMing

def heteronymProcess(chineseName:str) -> list:
    pinyinList = pypinyin.pinyin(chineseName,heteronym=True,style = pypinyin.Style.NORMAL)
    xing = pinyinList[0]
    mings = pinyinList[1:]
    names = []
    for letter in xing:
        name = {}
        name['xing'] = letter
        name['ming'] = extractMing(mings)
        names.append(name)
    return names

def generateNamePinyin(chineseName:str):
    #Jiangnan Liao
    #Jiang-Nan Liao
    #Liao Jiangnan
    #Liao Jiang-Nan
    #JN Liao
    #Liao JN
    forms = []
    possiblePinyinNames:list = heteronymProcess(chineseName)
    for dict in possiblePinyinNames:
        xing = dict['xing'].title()
        #Jiangnan Liao
        #Liao Jiangnan   
        for ming in dict['ming']:
            mingStr = ''
            for letter in ming:
                mingStr += letter
            mingStr = mingStr.title()
            forms.append(mingStr+' '+xing)
            forms.append(xing + ' ' + mingStr)
        #Jiang-Nan Liao
        #Liao Jiang-Nan
        for ming in dict['ming']:
            mingStr = ''
            for letter in ming:
                mingStr += letter.title() + ' '
            mingStr = mingStr.strip()
            if ' ' in mingStr:
                mingStr = mingStr.replace(' ','-')
            forms.append(mingStr+' '+xing)
            forms.append(xing + ' ' + mingStr)
        #JN Liao
        #Liao JN
        for ming in dict['ming']:
            mingStr = ''
            for letter in ming:
                mingStr += letter[0].capitalize()
            forms.append(mingStr+' '+xing)
            forms.append(xing + ' ' + mingStr)
    forms = list(set(forms))
    return forms

def WriteOperation(resDict):
    yearList = []
    for i in range(1990,2023):
        infoList = []
        year = str(i)
        infoList.append(resDict['publicationDict'].get(year))
        infoList.append(resDict['citationDict'].get(year))
        infoList.append(resDict['grantDict'].get(year))
        yearList.append(infoList)
    line = resDict['projectNum'] + ',' + resDict['name'] +',' +resDict['url'] +','+resDict['match']+','
    with open (Configs.Scraper2_Output_Data_Path,'a',encoding='utf-8') as resultFile:
        resultFile.write(line)
        for researchField in resDict['researchFields']:
            resultFile.write(researchField)
            resultFile.write(';')
        resultFile.write(',')
        for concept in resDict['concepts']:
            resultFile.write(concept)
            resultFile.write(';')
        resultFile.write(',')
        for education in resDict['educations']:
            resultFile.write(education)
            resultFile.write(';')   
        resultFile.write(',')
        for infoList in yearList:
            for info in infoList:
                if info == None:
                    resultFile.write('0')
                    resultFile.write(',')
                else:
                    resultFile.write(info)
                    resultFile.write(',')
        resultFile.write('\n')

def main():
    preprocessFile.con()
    with open(Configs.Scraper2_Input_Data_Path,'r',encoding='utf-8') as f:
        searchList = csv.reader(f)
        for searchInfo in searchList:
            projectNums = []
            projectNumsStr = searchInfo[1]
            if len(searchInfo[0])>3:
                with open('specialName.csv','a',encoding='utf-8') as f:
                    f.write(searchInfo[0]+','+searchInfo[1]+'\n')
                continue
            researchName:list = generateNamePinyin(searchInfo[0])
            projectNums = projectNumsStr.split('.')
            info = search(projectNums,researchName)
            WriteOperation(info)

#getResearchersPage(['21306007','21306008'])
#search(['21401178','21401179'],['Guohong Zou','a'])
if __name__ == '__main__':
    main()