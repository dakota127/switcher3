#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class Aktor_5
#   
#   Diese Class impmentiert das pyhsische Schalten der Dosen 
#
#   diese Class erbt von der MyPrint Class
#   
#   Version mit send Module (Habi).
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
import RPi.GPIO as GPIO         #  Raspberry GPIO Pins
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.myconfig import ConfigRead
 
DEBUG_LEVEL0=0                      
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

config_section = "aktor_5"  
progname = "swc_aktor5 "
OFFON = ['AUS','EIN']

# ***** Variables *****************************
#   Struktur (Directory) der Daten, die aus dem Configfile swconfig.ini gelesen werden
#   hier die defaultwerte der 'variablen'
# Abschnitt Aktor_5
cfglist_akt = {
        "gpio_send" : 0,    
        "system_code" : '11101',
        "pfad_1"        : '/home/pi/switcher2/' ,
}                                             
#----------------------------------------------------
# Class Definition Aktor, erbt vom MyPrint
#----------------------------------------------------
class Aktor_5 (MyPrint):
    ' klasse aktor '
    aktorzahler=0               # Class Variable

    def __init__(self, dosennummer,debug_in , config_filename_in):  # Init Funktion
        self.errorcode = 8           # init wert beliebig aber not zero

        self.nummer = Aktor_5.aktorzahler
        self.debug=debug_in
        self.config_file = config_filename_in          

        self.dosennummer=dosennummer            # arbeite für diese Dose (1 bis n)
        self.code=""
        self.pfad=""
        self.commandline=""
        self.pin=0
        GPIO.setmode (GPIO.BCM)
        rev=GPIO.RPI_REVISION
        GPIO.setwarnings(False)             # juni2018 ist neu hier, war in gpio_setup()

        
        self.action_type="Funk bei Habi"     # welche art Schalten ist dies hier
        
        self.myprint (DEBUG_LEVEL2,  progname + "aktor_init called für Dose:{}".format (self.dosennummer))
        Aktor_5.aktorzahler +=1            # erhögen aktorzähler

 # nun alle GPIO Pins aus dem Config File holen
        
        config=ConfigRead(self.debug)        # instanz der ConfigRead Class
        ret = config.config_read(self.config_file, config_section, cfglist_akt)
        if ret > 0:
            self.myprint (DEBUG_LEVEL1,  progname + "config_read hat retcode:{}".format (ret))
            self.errorcode=99
            return None




          # get values fro config file
        try:
            self.pin = int(cfglist_akt["gpio_send"])   
            self.code = cfglist_akt["system_code"]
            self.pfad = cfglist_akt["pfad_1"]
        except KeyError :
            self.myprint (DEBUG_LEVEL0,  progname + "KeyError in cfglist_akt, check values!")   

        self.myprint (DEBUG_LEVEL2,  progname + "aktor_init : dose:{}, using code:{} und pfad:{} und pin:{}".format (self.dosennummer, self.code, self.pfad,self.pin))

        self.commandline = "sudo " + self.pfad + "/send" + " " + str(self.pin)+ " " + self.code + " " + str(self.dosennummer) + " "
        self.myprint (DEBUG_LEVEL3,  progname + "aktor_init : dose:{}, using commandline:{}".format (self.dosennummer, self.commandline))
       

# **************************************************  
#-------------------------------------------
# __repr__ function Aktor_5
# 
    def __repr__ (self):

        rep = "Aktor_5 (Für Dose" + str(self.dosennummer) + "," + self.action_type  + ")"
        return (rep)



#-------------Terminate Action PArt ---------------------------------------
# cleanup GPIO PIns
#------------------------------------------------------------------------
    def __del__(self):
        self.myprint (DEBUG_LEVEL3,  progname + "del called")
       
        pass


# ***** Function zum setzen GPIO *********************
    def schalten(self,einaus,debug_level_mod):
  
        self.myprint (debug_level_mod,  progname + "schalten called:[{}]".format(OFFON[einaus]))
#
        
        self.cmd = self.commandline + str(einaus)
        ret = os.system(self.cmd)
        time.sleep(1.2)                     # wenn mehrer setSwitch hintereinander kommen, muss man warten  
   
        if ret >0:
            self.myprint (DEBUG_LEVEL0,  progname + "dose:{}, send module nicht gefunden:{}".format (self.dosennummer, self.cmd))
      
        return (ret)                  # return code
   
# ************************************************** 		


#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swc_aktor_5.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
