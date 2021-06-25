#!/usr/bin/python
# coding: utf-8
# ***********************************************************
# 	Programm zum Testen des TestAufbaus
# 
#   Alle Led's werden eingeschaltet auf Tastendruck
#   
#-------------------------------------------------
#
import sys
from time import sleep
from datetime import date, datetime, timedelta
import json


status_wetter_innen = [
               ["Temperatur Innen", "24.4" ],
               ["Feuchtigkkeit Innen","55.5" ],
               ["Letzte Messung um", "12.44 " ],              
               ["Max.Temp. Innen", "27.6" ],
               ["War am", "12.5.2018" ], 
               ["Min.Temp. Innen", "19.3" ],
               ["War am", "01.01.2018" ], 
               ["Max.Feucht. Innen", "88.4" ],
               ["War am", "02.03.2017" ], 
               ["Min.Feucht. Innen", "88.9" ],
               ["War am", "12.06.2016" ], 
               ["Batterie Innen", "1"],            

                ]

status_wetter_aussen = [
               ["Temperatur Aussen", "12.5" ],
               ["Feuchtigkkeit Aussen","15.9" ],
               ["Letzte Messung um", "08.12" ],              
               ["Max.Temp. Aussen", "19.6" ],
               ["War am", "12.12.2015" ], 
               ["Min.Temp. Aussen", " " ],
               ["War am", " " ], 
               ["Max.Feucht. Aussen", " " ],
               ["War am", " " ], 
               ["Min.Feucht. Aussen", " " ],
               ["War am", " " ], 
               ["Batterie Aussen", "0"],            

                ]
   
status_we = []           


# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    print ("Liste:")
    print (type(status_wetter_innen))
    print (status_wetter_innen)
    stati = json.dumps(status_wetter_innen)
    print (type(stati))
    print ("json:")
    print (stati)
  
    meld=json.loads(stati)   # JSON Object wird in Python List of List gewandelt
    print ("Liste:")
    print (type(meld))
    print (meld)   
    
    status_we.append(status_wetter_innen)
    status_we.append(status_wetter_aussen)
   
    
    print ("Liste:")
    print (type(status_we))
    print (status_we)
    stati = json.dumps(status_we)
    print (type(stati))
    print ("json:")
    print (stati)
  
    meld=json.loads(stati)   # JSON Object wird in Python List of List gewandelt
    print ("Liste:")
    print (type(meld))

    print (meld[0])    
    print (meld[1])    
 
 #---------------------------------------------
 #
    