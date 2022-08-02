import csv
import Configs
from selenium import webdriver
from selenium.webdriver.common.by import By
import pypinyin
from bs4 import BeautifulSoup
from time import sleep
import re
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
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

def Search(projectNum:str,names:list):
    url = "https://app.dimensions.ai/discover/publication?search_mode=content&search_text="+projectNum+"&search_type=kws&search_field=full_search"
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome()
    driver.implicitly_wait(60)
    driver.get(url)
    # 初始化一个等待器
    wait = WebDriverWait(driver,timeout=10,poll_frequency=0.5)
    wait.until(expected_conditions.element_to_be_clickable(("xpath",'//*[@id="onetrust-accept-btn-handler"]')))
    sleep(2)
    driver.find_element(By.XPATH,'//*[@id="onetrust-accept-btn-handler"]').click()
    for i in range(1,6):
        blankDict = {
        'projectNum':projectNum,
        'name':names[0],
        'publicationDict': {},
        'citationDict': {},
        'grantDict' : {},
        'researchFields': [],
        'concepts': [],
        'educations':[],
        'match': 'n'
    }
        try:
            wait = WebDriverWait(driver,timeout=30,poll_frequency=0.5)
            wait.until(expected_conditions.element_to_be_clickable(("xpath",'//*[@id="analytics-contents"]/div[3]/div/div/ul/li[1]/div[1]/a')) and expected_conditions.visibility_of_element_located(('xpath','//*[@id="analytics-contents"]/div[3]/div/div/ul/li[1]/div[1]/a')))
            researcherName = driver.find_element(By.XPATH,'//*[@id="analytics-contents"]/div[3]/div/div/ul/li['+str(i)+']/div[1]/a').text
        except (NoSuchElementException,TimeoutException):
            with open('noFound.txt','a',encoding='utf-8') as f:
                line = projectNum + ' ' + names[0] + '\n'
                f.write(line)
                return blankDict
        if researcherName in names:
            name = researcherName
            #click the name
            wait = WebDriverWait(driver,timeout=10,poll_frequency=0.5)
            wait.until(expected_conditions.element_to_be_clickable(("xpath",'//*[@id="analytics-contents"]/div[3]/div/div/ul/li['+str(i)+']/div[1]/a')))
            sleep(2)
            driver.find_element(By.XPATH,'//*[@id="analytics-contents"]/div[3]/div/div/ul/li['+str(i)+']/div[1]/a').click()
            #click view profile
            wait = WebDriverWait(driver,timeout=20,poll_frequency=0.5)
            wait.until(expected_conditions.element_to_be_clickable(("xpath",'//*[@id="mainContentBlock"]/div/div/div/div[1]/header/div[2]/div[2]/a')))
            sleep(3)
            driver.find_element(By.XPATH,'//*[@id="mainContentBlock"]/div/div/div/div[1]/header/div[2]/div[2]/a').click()
            sleep(2)
            #scrap page info
            wait = WebDriverWait(driver,timeout=60,poll_frequency=0.5)
            wait.until(expected_conditions.visibility_of_element_located(('xpath','//*[@id="mainContentBlock"]/div/article[1]/div/section[2]/div/ol')) and expected_conditions.visibility_of_element_located(('xpath','//*[@id="mainContentBlock"]/div/article[1]/div/section[1]/div/ol')) 
            and expected_conditions.visibility_of_element_located(('xpath','.//div[@class = "highcharts-container "]')))
            sleep(5)
            pageContent = BeautifulSoup(driver.page_source,'lxml')
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
                'match':'y'
            }
            return resDict
    return blankDict

def WriteOperation(resDict):
    yearList = []
    for i in range(1990,2023):
        infoList = []
        year = str(i)
        infoList.append(resDict['publicationDict'].get(year))
        infoList.append(resDict['citationDict'].get(year))
        infoList.append(resDict['grantDict'].get(year))
        yearList.append(infoList)
    line = resDict['projectNum'] + ',' + resDict['name'] +',' +resDict['match']+','
    with open (Configs.Scraper1_Output_Data_Path,'a',encoding='utf-8') as resultFile:
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
    with open(Configs.Scraper1_Input_Data_Path,'r',encoding='utf-8') as f:
        searchList = csv.reader(f)
        for searchRequire in searchList:
            name = pypinyin.lazy_pinyin(searchRequire[0])
            ming = ''
            for i in range(0,len(name)):
                if i == 0:
                    xing = name[i].title()
                else:
                    ming+= (name[i].title()+' ')
            ming = ming.strip(' ')
            ming = ming.replace(' ','-')
            form1 = ming + ' ' + xing
            ming1 = ''
            for i in range(0,len(name)):
                if i == 1:
                    ming1 += name[i].title()
                elif i == 0:
                    continue
                else:
                    ming1 += name[i]
            form2 =ming1 +' '+xing
            forms = [form1,form2]
            resDict = Search(searchRequire[1],forms)
            WriteOperation(resDict)
        
if __name__ == '__main__':
    main()