#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class Wetter 
#   
#   Diese Class speichert Wetterdaten und gibt siw wieder aus auf verlangen  
#
#   diese Class erbt von der MyPrint Class
#   
#
#   folgende public methods stehen zur Verfügung:
#       store_wetter_data()     wetterdaten des Sensors versorgen
#       get_wetter_data_all()   ALLE wetterdaten liefern als Liste
#       get_wetter_data_part()  Nur Temperaturen liefern als Liste

#   Oktober 2018
#************************************************
#
import os
import sys
import time
from time import sleep
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
# from sub.myconfig import ConfigRead
from sub.swdefstatus import status_wetter_innen         # Struktur (Liste) für Indoor Statusmeldung)
from sub.swdefstatus import status_wetter_aussen        # Struktur (Liste) für Outdoor Statusmeldung)
import json
from datetime import date, datetime, timedelta

DEBUG_LEVEL0=0                      
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

progname = "swc_wetter "

#----------------------------------------------------
# Class Definition Wetter, erbt vom MyPrint
#
#----------------------------------------------------
class Wetter (MyPrint):
    ' klasse wetter '
    wetterzahler=0               # Class Variable
    
   
    def __init__(self,debug_in , path_in, mqtt_instanz):  # Init Funktion
        self.errorcode = 8
        self.nummer = Wetter.wetterzahler
        self.debug=debug_in
        self.path = path_in          # pfad  main switcher
        self.mqttc = mqtt_instanz
        self.myprint (DEBUG_LEVEL1, progname + "wetter_init() called ")
        Wetter.wetterzahler +=1            # erhögen wetterzähler
        self.intemp = 0
        self.outtemp = 0
        self.elapsed_time = ""
        self.inoutdoor = 0
        self.tempe = 0
        self.humi = 0
        self.woher = ""
        self.temp = 0
        self.hum = 0
        self.bat = ""                       # batterie Zustand string
        self.sensor = ""                    # sensor status
        self.anzahl_meldungen = 0
        self.dattime = 0
        self.timenow = 0
        self.intervall_1 = 3600                # in Sekunden, also: 3600 / 60  gleich 60 min 
        self.intervall_2 = 11800                # in Sekunden, also: 11800 / 60  gleich 180 min 
        
        self.dattime = datetime.now().strftime("%d.%m.%Y / %H.%M")
        self.timenow = datetime.now().strftime("%H.%M")  # Zeit der meldung
        self.wetterlist = []

 #      liste of list: hier werden die Wetterdaten versorgt 
        self.wetter_data = [ [0 for i in range(17)] for z in range(2) ]

        self.wetter_data [0][0] = ""         # init  werte       sensor status
        self.wetter_data [1][0] = ""        # init  werte       sensor status

        self.wetter_data [0][1] = self.dattime         # init  werte
        self.wetter_data [1][1] = self.dattime         # init  werte
        self.wetter_data [0][2] = 0         # init  werte nichts gekommen
        self.wetter_data [1][2] = 0         # init  werte
        self.wetter_data [0][3] = ""         # init  werte
        self.wetter_data [1][3] = ""         # init  werte
        self.wetter_data [0][8] = ""         # init  werte
        self.wetter_data [1][8] = ""         # init  werte
        self.wetter_data [0][10] = ""         # init  werte
        self.wetter_data [1][10] = ""         # init  werte
        self.wetter_data [0][12] = ""         # init  werte
        self.wetter_data [1][12] = ""         # init  werte
        self.wetter_data [0][14] = ""         # init  werte
        self.wetter_data [1][15] = ""         # init  werte
        self.wetter_data [0][16] = ""         # init  werte
        self.wetter_data [1][16] = ""         # init  werte
        self.wetter_data [0][9] = 99         # init minmale werte
        self.wetter_data [0][13] = 99         # init minmale werte
        self.wetter_data [1][9] = 99         # init minmale werte
        self.wetter_data [1][13] = 99         # init minmale werte
# wetter_data = [ [0 for z in range(8)] for z in range(2) ]
                                    # Liste mit 2 Listen, jeweils:
                                    # index 0: Sensorstatus, string vom sensor geliefert, init "nicht bekannt"
                                    # index 1: datumzeit des status
                                    # index 2: fehlercode
                                    # index 3: Zeit letzte gemommene Meldung (string)
                                    # index 4: Zeit letzte gemommene Meldung (datetime)
                                    # index 5: Indoor Temp
                                    # index 6: Indoor Humidity
                                    # index 7: maximale Temp
                                    # index 8: Datum maximale Temp
                                    # index 9: minimale Temp
                                    # index 10: Datum minimale Temp
                                    # index 11: maximale Humidity
                                    # index 12: Datum maximale Humidity
                                    # index 13: minimale Humidity
                                    # index 14: Datum minimale Humidity
                                    # index 15: battery status (string von sensor)
                                    # index 16: elapsed time (string von sen
        self.inout = {0:'Indoor', 1:'Outdoor'}  
     
        self.errorcode=0    # init aktor ok

        self.wetter_data[0][4] = datetime.now()          # Init
        self.wetter_data[1][4] = datetime.now()          # Init

    #   subscribe to mqtt broker
        self.mqttc.subscribe_topic ("swi/wetter/data" , self.store_wetter_data)    # subscribe to topic wetterdaten
        self.mqttc.subscribe_topic ("swi/wetter/lw" , self.last_will)              # subscribe to Last Will Topic der Sensoren

#   Ende init Wetter Klasse


#-------------------------------------------
# __repr__ function class Wetter
# 
    def __repr__ (self):

        rep = "Wetter (" +  self.dattime  + ", debug:{})".format(self.debug)
        return (rep)


#---- last_will -----------------
#  this function a callback fuction, it is called if a mqtt message is received on topic
#  "switcher/wetter/lw"
#---------------------------------------------------------------
# hier kommt Last Will and Testament des Sensors rein (siehe Arduino Code für ESP8266)
#
    def last_will(self,payload):
        self.myprint (DEBUG_LEVEL2, progname + "last_will() called  payload: {}".format( payload))
        if  payload.find("indoor") >= 0:
            self.wetter_data [0][0] = 2             # status = 2  wenn last will gekommen ist
            self.wetter_data [0][1] = self.dattime   # datum/zeit dazu
            self.wetter_data[0][2] = 0               # clear error code
            return
        if  payload.find("outdoor") >= 0:    
            self.wetter_data [1][0] = 2            # status = 2  wenn last will gekommen ist
            self.wetter_data [1][1] = self.dattime   # datum/zeit dazu
            self.wetter_data[1][2] = 0               # clear error code


#--- Funktion Behandlung Wetterdaten------------------------------
#  this function a callback fuction, it is called if a mqtt message is received on topic
#  "switcher/wetter/data"
#---------------------------------------------------------------
    def store_wetter_data (self, client, userdata, message):
    
        payload = message.payload.decode()      # payload ist ON oder OFF
        self.anzahl_meldungen += 1       # erhöhe anzahl meldungen
#       print ("store wetterdata called")
        self.myprint (DEBUG_LEVEL2, progname + "store_wetter_data() called  payload: {}".format( payload))
    
        #  die payload auswerten, alles getrennt mit /.
        try:
            self.woher, self.bat, self.sensor, self.elapsed_time, self.temp, self.hum,  = payload.split('/')

        except:
            self.myprint (DEBUG_LEVEL0,progname + "store_wetter_data(): mqtt callback split nicht ok")

            return
      # testing:
      #  print ("Wetterdaten gekommen:")
      #  print (self.woher, self.temp, self.hum, self.bat, self.elapsed_time, self.sensor)
      #  print (type(self.elapsed_time))
    
        self.inoutdoor = -8
        if  self.woher.find("outdoor") >= 0:
            self.myprint (DEBUG_LEVEL2,progname + "meldung von outdoor sensor gekommen") 
            self.inoutdoor = 1
            
        if  self.woher.find("indoor") >= 0:
            self.myprint (DEBUG_LEVEL2,progname + "meldung von indoor sensor gekommen") 
            self.inoutdoor = 0

        if self.inoutdoor < 0:
            self.myprint (DEBUG_LEVEL0,progname + "meldung payload nicht indoor oder outdoor: {}".format(self.woher))
            return
            
        self.dattime = datetime.now().strftime("%d.%m.%Y / %H.%M")
        self.timenow = datetime.now().strftime("%H.%M")  # Zeit der meldung

            
 # nun datem versorgen in der Liste       
              
        self.tempe = float(self.temp)
        self.humi = float (self.hum)
#        print (self.tempe, self.humi,self.inoutdoor)
        if self.tempe == -999 or self.humi == -999:       
            self.wetter_data[self.inoutdoor][2] = 9     # fehler 9 error reading sensor, wird so geliefert von der
                                                        # library dhtnew.cpp
            self.myprint (DEBUG_LEVEL0,progname + "Error reading sensor erhalten von: {}".format (self.inout[self.inoutdoor])) 
            return                                      # wir können nichts versorgen, also fertig  
 
 # nun machen wir noch Plausicheck
        if self.tempe > 60 or self.tempe < -25 :
            self.myprint (DEBUG_LEVEL0,progname + "Temperatur nicht plausibel: {}  von: {}".format (self.tempe, self.inout[self.inoutdoor])) 
            return
        if self.humi > 100 or self.tempe < 1 :
            self.myprint (DEBUG_LEVEL0,progname + "Humidity nicht plausibel: {}  von: {}".format (self.humi, self.inout[self.inoutdoor])) 
            return
# Werte ok, wir speichern....

        self.wetter_data[self.inoutdoor][2] = 1      # 1: eine Meldung gekommen
        self.wetter_data[self.inoutdoor][3] = self.dattime          # Zeit der meldung
        self.wetter_data[self.inoutdoor][4] = datetime.now()          # Zeit der meldung

        self.wetter_data[self.inoutdoor][5] = self.tempe           # Temp
        self.wetter_data[self.inoutdoor][6] = self.humi           # humidity
        
#        print (self.tempe, self.humi,self.bat, self.inoutdoor)

        if self.wetter_data[self.inoutdoor][7] < self.tempe:       # maximale temperatur
            self.wetter_data[self.inoutdoor][7] = self.tempe
            self.wetter_data[self.inoutdoor][8] =  self.dattime       # Datum/Zeit
            self.myprint (DEBUG_LEVEL3, progname + "max temp found, {}".format(self.inout[self.inoutdoor]))

        if self.wetter_data[self.inoutdoor][9] >  self.tempe:       # minimale temp
            self.wetter_data[self.inoutdoor][9] = self.tempe          
            self.wetter_data[self.inoutdoor][10] =  self.dattime      # Datum/Zeit
            self.myprint (DEBUG_LEVEL3,progname +  "min temp found, {}".format(self.inout[self.inoutdoor]))
    
        if self.wetter_data[self.inoutdoor][11] < self.humi :       # maximale humidity
            self.wetter_data[self.inoutdoor][11] = self.humi
            self.wetter_data[self.inoutdoor][12] =  self.dattime # Datum/Zeit
            self.myprint (DEBUG_LEVEL3,progname + "max humi found, {}".format(self.inout[self.inoutdoor]))
            
        if self.wetter_data[self.inoutdoor][13] >  self.humi:       # minimale humidity     
            self.wetter_data[self.inoutdoor][13] = self.humi   
            self.wetter_data[self.inoutdoor][14] =  self.dattime    # Datum/Zeit
            self.myprint (DEBUG_LEVEL3,progname +  "min humi found, {}".format(self.inout[self.inoutdoor]))
    
        
        self.wetter_data[self.inoutdoor][15] = self.bat    # battery level
        self.wetter_data[self.inoutdoor][16] = self.elapsed_time
        self.wetter_data [self.inoutdoor][0] = self.sensor  # sensor status
        
        # nun noch status setzen      
 #       if not self.wetter_data [self.inoutdoor][0] == 1:          # verändere, wenn anders als 1 (verbunden) ist
  #          self.wetter_data [self.inoutdoor][0] = 1            # setze sensorstatus auf 1 (verbunden)
   #         self.wetter_data [self.inoutdoor][1] = self.dattime   # datum/zeit dazu
     

        self.myprint (DEBUG_LEVEL2, progname + "Wetterdata indoor:  {}".format(self.wetter_data[0]))
        self.myprint (DEBUG_LEVEL2, progname + "Wetterdata outdoor: {}".format(self.wetter_data[1]))
    
        return
  
    pass
    
    
# ---- private method delta time --------------
    def time_delta(self, time_old, woher):          # woher ist indoor oder outdoor
       
        
        delta = datetime.now() - time_old
        delta = int(delta.days * 24 * 3600 + delta.seconds)     # delta in sekunden    

        if delta > self.intervall_2:              #   180 minuten vorbei ?
            self.myprint (DEBUG_LEVEL0,progname + "schon > 3 Stunde keine Meldung bekommen von {}".format (self.inout[woher]))
            return (2," **!!!**" )

        if delta > self.intervall_1:              #   60 minuten vorbei ?
            self.myprint (DEBUG_LEVEL0,progname + "schon > 1 Stunde keine Meldung bekommen von {}".format (self.inout[woher]))
            return (1," **!**")
                   
        return(0,"")

#  -----------------------------------------------------------           
# ---- public method get wetter_data   -----------------------
#       retuns a list of two lists (indoor and outdoor values)
#-------------------------------------------------------------
    def get_wetter_data_all(self):
 
        self.myprint (DEBUG_LEVEL1,progname + "get_wetter_data_all() called  ")

# indoor behandeln
        if  self.wetter_data[0][2] == 0:    # nichts gekommen von indoor
            self.intemp = "Noch Keine Werte"   
        else:
            self.intemp = str(self.wetter_data[0][5])       # temp indoor
            ret, stri = self.time_delta (self.wetter_data[0][4],0)    # letzte Messung indoor
            self.intemp = self.intemp + stri 

        if self.wetter_data[0][2] == 9:
            self.intemp = " Fehler Read Sensor"

# dann outdoor behandeln   
        if  self.wetter_data[1][2] == 0:    # check sensorstatus  0: nichts gekommen von outdoor
            self.outtemp = "Noch keine Werte"   
        else:
            self.outtemp = str(self.wetter_data[1][5])
            ret, stri = self.time_delta (self.wetter_data[1][4], 1)   # letzte Messung outdoor
            self.outtemp = self.outtemp + stri
      
        if self.wetter_data[1][2] == 9:
            self.intemp = " Fehler Read Sensor"
            
            
# nun abfuellen in die Liste Indoor

        status_wetter_innen[0][1] = self.intemp                # in temp
        status_wetter_innen[1][1] = str(self.wetter_data[0][6])     # in feucht
        status_wetter_innen[2][1] = self.wetter_data[0][3]     # datim/zeit last meldung
        
        status_wetter_innen[3][1] = str(self.wetter_data[0][7])    # max temp innen
        status_wetter_innen[4][1] = self.wetter_data[0][8]     # datum dazu
        status_wetter_innen[5][1] = str(self.wetter_data[0][9])     # min temp innen
        status_wetter_innen[6][1] = self.wetter_data[0][10]     # datum dazu
        

        status_wetter_innen[7][1] = str(self.wetter_data[0][11])     # max feucht innen
        status_wetter_innen[8][1] = self.wetter_data[0][12]     # datum dazu
        status_wetter_innen[9][1] = str(self.wetter_data[0][13])     # min feuch innen
        status_wetter_innen[10][1] = self.wetter_data[0][14]     # datum dazu
     
        status_wetter_innen[11][1] = str(self.wetter_data[0][15])     # batterie innen
        status_wetter_innen[12][1] = self.wetter_data[0][0]     # sensorstatus     
        status_wetter_innen[13][1] = self.wetter_data[0][16]     # dauer im ms  (sensor)    


        
# nun outdoor
        status_wetter_aussen[0][1] = self.outtemp               # out temp
        status_wetter_aussen[1][1] = str(self.wetter_data[1][6])     # out feucht
        status_wetter_aussen[2][1] = self.wetter_data[1][3]     # datum/zeit last meldung out

        status_wetter_aussen[3][1] = str(self.wetter_data[1][7])     # max temp aussen
        status_wetter_aussen[4][1] = self.wetter_data[1][8]     # datum dazu
        status_wetter_aussen[5][1] = str(self.wetter_data[1][9])     # min temp aussen
        status_wetter_aussen[6][1] = self.wetter_data[1][10]     # datum dazu

        status_wetter_aussen[7][1] = str(self.wetter_data[1][11])     # max feucht aussen
        status_wetter_aussen[8][1] = self.wetter_data[1][12]     # datum dazu
        status_wetter_aussen[9][1] = str(self.wetter_data[1][13])     # min feucht aussen
        status_wetter_aussen[10][1] = self.wetter_data[1][14]     # datum dazu

        status_wetter_aussen[11][1] = str(self.wetter_data[1][15])     # batterie aussen

        status_wetter_aussen[12][1] = self.wetter_data[1][0]     # sensorstatus             
        status_wetter_aussen[13][1] = self.wetter_data[1][16]     # dauer im ms  (sensor)      
        
        
        
        self.myprint (DEBUG_LEVEL2,progname + "sende Innen:  {} ".format(status_wetter_innen))
        self.myprint (DEBUG_LEVEL2,progname + "sende Aussen: {}".format(status_wetter_aussen))
        
        self.wetterlist = []
        self.wetterlist.append(status_wetter_innen)
        self.wetterlist.append(status_wetter_aussen)
        
 #       stati=json.dumps(self.wetterlist)
 #       return(stati)                               # Meldungs-ID vorne anhaengen (Statusmeldung)
        return(self.wetterlist)
        
# ---- public method get wetter_data   -------------------------------
    def get_wetter_data_part(self):
        self.myprint (DEBUG_LEVEL1,progname + "get_wetter_data_part() called  ")

# zuerst inddor behandeln

        if  self.wetter_data[0][2] == 0:   # check fehlercode  0: noch keine meldung gekommen
            self.intemp = "Noch keine Werte"   
        elif self.wetter_data[0][0] == 2:   # check sensorstatus  2: Verbindung verloren
            self.intemp = "Verbindung unterbrochen"    
        else:
            self.intemp = str(self.wetter_data[0][5])
            ret, stri= self.time_delta (self.wetter_data[0][4],0)
            self.intemp = self.intemp + stri 
          
        if self.wetter_data[0][2] == 9:
            self.intemp = " Fehler Read Sensor"

        
# dann outdoor behandeln   
        if  self.wetter_data[1][2] == 0:   # check fehlercode  0: noch keine meldung gekommen
            self.outtemp = "Noch keine Werte"   
        elif self.wetter_data[1][0] == 2:   # check sensorstatus  2: Verbindung verloren
            self.outtemp = "Verbindung unterbrochen"    
        else:
            self.outtemp = str(self.wetter_data[1][5])
            ret, stri = self.time_delta (self.wetter_data[1][4],1)
            self.outtemp = self.outtemp + stri
   
        if self.wetter_data[1][2] == 9:
            self.intemp = " Fehler Read Sensor"
 
        return (self.intemp,self.outtemp)
         
    

#-------------Terminate Action PArt ---------------------------------------
# cleanups
#------------------------------------------------------------------------
    def __del__(self):
    
        pass

#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swc_wetter.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
