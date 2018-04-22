import os
import sys
import pickle

data = (34.058250,-117.82232,160,5)
fileObject = open("gps.pkl","wb") 
pickle.dump(data,fileObject)   
fileObject.close()