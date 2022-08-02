import csv
import Configs
def con():
    with open(Configs.preprocess_File_Input_Path,'r',encoding='utf-8') as f:
        searchList = list(csv.reader(f))
        for i in range(1,len(searchList)):
            projectNums = []
            researchName = searchList[i][2]
            if researchName != searchList[i-1][2]:
                for j in range(i,len(searchList)):
                    if searchList[j][5] == searchList[j+1][5]:
                        projectNums.append(searchList[j][1])
                    else:
                        projectNums.append(searchList[j][1])
                        break
                with open('3.1.csv','a',encoding='utf-8') as f1:
                    projectNumStr = ''
                    for projectNum in projectNums:
                        projectNumStr += str(projectNum)+ '.'
                    projectNumStr = projectNumStr.rstrip('.')
                    line = researchName + ',' + projectNumStr
                    f1.write(line+'\n')
            else:
                continue
con()
