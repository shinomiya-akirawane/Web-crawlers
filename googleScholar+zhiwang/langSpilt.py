import csv
import dimensions.Configs as Configs
class Split():
    def __init__(self) -> None:
        pass
    def extractTitle(self,line):
        return line[4]

    def spilt(self):
        with open (Configs.dataPath,'r',encoding='utf-8') as myFile:
            lines = csv.reader(myFile)
            for line in lines:
                cnt = 0
                title = self.extractTitle(line)
                for letter in title:
                    if (ord(letter) >=65 and ord(letter) <=90) or (ord(letter) >=97 and ord(letter) <=122):
                        cnt+=1
                if (cnt/len(title) > 0.6):
                    with open(Configs.splitResultPath+'en.csv','a',encoding='utf-8') as en:
                        enWriter = csv.writer(en)
                        enWriter.writerow(line)
                else:
                    with open(Configs.splitResultPath+'zh.csv','a',encoding='utf-8') as zh:
                        zhWriter = csv.writer(zh)
                        zhWriter.writerow(line)
        zh.close()
        en.close()
