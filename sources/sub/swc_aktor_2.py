#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class Aktor_2 
#   
#   Diese Class impmentiert das pyhsische Schalten der Dosen 
#
#   diese Class erbt von der MyPrint Class
#   
#   Version für Funksteckdosen mit einem 433 MHz Sender an einem GPIO Pin.
#
#   folgende public methods stehen zur Verfügung:
#       schalten (ein_aus)     ein_aus ist entweder 0 oder 1
#   
#   Juli 2018
#************************************************
#
import os
import sys
import time
from time import sleep
# import RPi.GPIO as GPIO         #  Raspberry GPIO Pins
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.myconfig import ConfigRead
from sub.rpi_rf import RFDevice

                 
DEBUG_LEVEL0 = 0
DEBUG_LEVEL1 = 1
DEBUG_LEVEL2 = 2
DEBUG_LEVEL3 = 3

config_section = "aktor_2"
progname = "swc_aktor2 "

OFFON = ['AUS','EIN']

# ***** Variables *****************************
#   Struktur (Directory) der Daten, die aus dem Configfile swconfig.ini gelesen werden
#   hier die defaultwerte der 'variablen'
cfglist_akt = {
        "gpio_1"    : 17,
        "repeat"    : 10,
        "codelength" : 24,
        "send_dat_1_ein" : "66897,320,1",
        "send_dat_1_aus" : "66900,319,1",
        "send_dat_2_ein" : "69983,319,1",
        "send_dat_2_aus" : "69972,319,1",
        "send_dat_3_ein" : "70737,319,1",
        "send_dat_3_aus" : "70740,319,1",
        "send_dat_4_ein" : "70929,320,1",
        "send_dat_4_aus" : "70932,319,1",
}  

#----------------------------------------------------
# Class Definition Aktor_3, erbt vom MyPrint
#----------------------------------------------------
class Aktor_2 (MyPrint):
    ' klasse aktor '
    aktorzahler = 0               # Class Variable
    
    def __init__(self, dosennummer,debug_in, config_filename_in):  # Init Funktion
        self.errorcode = 8
        self.nummer = Aktor_2.aktorzahler
        self.debug = debug_in
        self.dosennummer = dosennummer            # arbeite für diese Dose (1 bis n)
        self.config_file = config_filename_in          # pfad  main switcher

        self.action_type = "Funk2"     # welche art Schalten ist dies hier
        self.mypin = 0
        self.repeat = 1
        self.codel = 0
        self.data_ein = ""
        self.data_aus = ""
        self.myprint (DEBUG_LEVEL2,  progname + "init called fuer Dose {}".format (self.dosennummer))
        Aktor_2.aktorzahler += 1            # erhögen aktorzähler
        
 # nun alle notwendigen Parameter aus dem Config File holen
        
        
        if (self.debug > 2):
            self.myprint (DEBUG_LEVEL3,  progname + "Configdictionary before reading:")
            for x in cfglist_akt:
                print ("{} : {}".format (x, cfglist_akt[x]))

        config = ConfigRead(self.debug)        # instanz der ConfigRead Class
        ret = config.config_read(self.config_file, config_section, cfglist_akt)        
        if ret > 0:
            self.myprint (DEBUG_LEVEL0,  progname + "config_read hat retcode:{}".format (ret))
            self.errorcode=99
            return None

        if (self.debug > 2):
            self.myprint (DEBUG_LEVEL3,  progname + "Configdictionary after reading:")
            for x in cfglist_akt:
                print ("{} : {}".format (x, cfglist_akt[x]))


       # get values fro config file
        try:
           
        #   zuerst den GPIO Pin für den 433 MHz Sender
            self.mypin = int(cfglist_akt["gpio_1"])         
        #   repeat für den 433 MHz Sender
            self.repeat = int(cfglist_akt["repeat"]) 
        #   codelengt für den 433 MHz Sender
            self.codel = int(cfglist_akt["codelength"])


        # nun die Switch Codes und die Pulse Lenghts
        #   zuerst die Parameter für das Einschalten
            such_base = "send_dat_" + str(self.dosennummer)
            such_ein = such_base+ "_ein" 
            self.data_ein = cfglist_akt[such_ein]
            self.data_ein = str(self.data_ein)    
        #   dann die Parameter für das Ausschalten
            such_aus = such_base+ "_aus"        
            self.data_aus = cfglist_akt[such_aus]
            self.data_aus = str(self.data_aus)
            
        except KeyError :
            self.myprint (DEBUG_LEVEL0,  progname + "KeyError in cfglist_akt, check values!")   


        self.myprint (DEBUG_LEVEL2,  progname + "init: Dose:{}, repeat:{} , codel:{}".format(self.dosennummer, self.repeat,self.codel))

#   

        self.swcode_ein,self.pulselength_ein,self.protocoll_ein = self.data_ein.split(",")
        
        self.myprint (DEBUG_LEVEL2,  progname + "init: Dose:{}, code:{} , length:{} , protocoll:{}".format(self.dosennummer, self.swcode_ein,self.pulselength_ein,self.protocoll_ein))
 
 #      For Testing       
 #       print (type(self.swcode_ein), self.swcode_ein)
 #       self.swcode_ein=self.swcode_ein.decode()
 #       print (type(self.swcode_ein), self.swcode_ein)
         
        self.swcode_ein = int(self.swcode_ein)
        self.pulselength_ein = int(self.pulselength_ein)
        self.protocoll_ein = int(self.protocoll_ein)
#   dann die Parameter für das Ausschalten
        
        
         
        self.swcode_aus,self.pulselength_aus,self.protocoll_aus=self.data_aus.split(",")
        self.myprint (DEBUG_LEVEL2,  progname + "init: Dose:{}, code:{}, length:{}, protocoll:{}".format(self.dosennummer, self.swcode_aus,self.pulselength_aus,self.protocoll_aus))
        self.swcode_aus = int(self.swcode_aus)
        self.pulselength_aus = int(self.pulselength_aus)
        self.protocoll_aus = int(self.protocoll_aus)

  
  # verwende rfdevice  von hier  https://github.com/milaq/rpi-rf
        self.rfdevice = RFDevice(self.mypin,self.myprint)
        self.rfdevice.enable_tx()
        self.rfdevice.tx_repeat = self.repeat
 
        self.errorcode = 0          # aktor init ok



#-------------------------------------------
# __repr__ function Aktor_2
# 
    def __repr__ (self):

        rep = "Aktor_2 (Fr Dose"  + str(self.dosennummer) + "," + self.action_type  + ")"
        return (rep)


#       For Testing               
#        print (type(self.swcode_ein),type(self.pulselength_ein),type(self.protocoll_ein))
#        print (type(self.swcode_aus),type(self.pulselength_aus),type(self.protocoll_aus))
#        print (type(self.codel), type(self.repeat))
#-------------Terminate Action PArt ---------------------------------------
# delete instance
#------------------------------------------------------------------------
    def __del__(self):
        self.myprint (DEBUG_LEVEL3,  progname + "del called")
    
        pass

# ***** Function zum setzen GPIO *********************
    def schalten(self,einaus, debug_level_mod):
        global GPIO
  
        self.myprint (debug_level_mod,  progname + "dose{} schalten called, Gpio:{} [{}]".format(self.dosennummer,self.mypin, OFFON[einaus]))
#
        if einaus == 1:
            self.rfdevice.tx_code(self.swcode_ein, self.protocoll_ein, self.pulselength_ein, self.codel)
 #           self.rfdevice.cleanup()
        else:
            self.rfdevice.tx_code(self.swcode_aus, self.protocoll_aus, self.pulselength_aus, self.codel)
 #           self.rfdevice.cleanup()
        
        return (0)                  # return code immer null
         
   
# ************************************************** 		


#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swc_aktor_2.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
