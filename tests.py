import pandas as pd 
import numpy as np
import csv 
from matching_engine import MatchingEngine

#CASE 1 the orders are crossing the mid, mkt buy vs sell
# one negative price order 
d1 = pd.DataFrame(np.array([[1,'MSFT','MKT','Buy',-1],[2,'MSFT','MKT','Buy',100],[3,'MSFT',99,'Sell',90]]),columns=['OrderID','Symbol','Price','Side','OrderQuantity'])




#CASE 2 No market as both orders are limit
d2 = pd.DataFrame(np.array([[1,'MSFT',89,'Buy',100],[2,'MSFT',99,'Sell',90]]),columns=['OrderID','Symbol','Price','Side','OrderQuantity'])
d3 = pd.DataFrame(np.array([[1,'MSFT','MKT','Buy',1],[2,'MSFT',99,'lol',90]]),columns=['OrderID','Symbol','Price','Side','OrderQuantity'])
d4 = pd.DataFrame(np.array([[1,'MSFT',-100,'Buy',1],[2,'MSFT',99,'Sell',90]]),columns=['OrderID','Symbol','Price','Side','OrderQuantity'])
d4 = pd.DataFrame(np.array([[1,'MSFT',20,'Buy',-1],[2,'MSFT',99,'Sell',None]]),columns=['OrderID','Symbol','Price','Side','OrderQuantity'])



for df in [d1,d2]:
    engine = MatchingEngine()
    engine.load(file_path=None,df=df)
print("ok")