import pandas as pd
data_xls = pd.read_excel('3.xls', index_col=0)   
data_xls.to_csv('3.csv', encoding='utf-8')
