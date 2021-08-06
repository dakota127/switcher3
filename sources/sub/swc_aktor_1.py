#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class Akto_1 
#   
#   Diese Class impmentiert das pyhsische Schalten einer Dose
#
#   diese Class erbt von der MyPrint Class
#   
#   Version mit 4 LED - meist zum Testen verwendet.
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


config_section = "aktor_1"
progname = "swc_aktor1 "


OFFON = ['AUS','EIN']

# dict values from config file
cfglist_akt = {   
        "gpio_1"    : 12,
        "gpio_2"    : 19,
        "gpio_3"    : 20,
        "gpio_4"    : 21,
        "gpio_5"    : 24,
}

#----------------------------------------------------
# Class Definition Aktor, erbt vom MyPrint
#----------------------------------------------------
class Aktor_1 (MyPrint):
    ' klasse aktor '
    aktorzahler=0               # Class Variable
    
    def __init__(self, dosennummer,debug_in , config_filename_in):  # Init Funktion
        self.errorcode = 8
        self.nummer = Aktor_1.aktorzahler
        self.debug=debug_in
        self.dosennummer=dosennummer            # arbeite für diese Dose (1 bis n)
        self.Pins2=[]
        self.config_file = config_filename_in          # pfad  main switcher

        GPIO.setmode (GPIO.BCM)
        rev=GPIO.RPI_REVISION
        GPIO.setwarnings(False)             # juni2018 ist neu hier, war in gpio_setup()

        
        self.action_type="4 LED"     # welche art Schalten ist dies hier
        
        self.myprint (DEBUG_LEVEL2,   progname + "aktor_init called für Dose {}".format (self.dosennummer))
        Aktor_1.aktorzahler +=1            # erhögen aktorzähler

 # nun alle GPIO Pins aus dem Config File holen
 # es müssen 5 Pins definiert werden, da maximal 5 Dosen vorkommen können
        
        config=ConfigRead(self.debug)        # instanz der ConfigRead Class
        
        ret = config.config_read(self.config_file, config_section, cfglist_akt)
##        ret=config.config_read(self.path + "/swconfig.ini","aktor_1",cfglist_akt)
        if ret > 0:
            self.myprint (DEBUG_LEVEL0,   progname +  "config_read hat retcode: {}".format (ret))
            self.errorcode=99
            return None



        # get values fro config file
        try:
        #   GPIO Pin 1 holen
            self.Pins2.append (int(cfglist_akt["gpio_1"]))
        #   GPIO Pin 2 holen
            self.Pins2.append (int(cfglist_akt["gpio_2"]))
        #   GPIO Pin 3 holen
            self.Pins2.append (int(cfglist_akt["gpio_3"]))
        #   GPIO Pin 4 holen
            self.Pins2.append (int(cfglist_akt["gpio_4"]))
        #   GPIO Pin 5 holen
            self.Pins2.append (int(cfglist_akt["gpio_5"]))
        except KeyError :
            self.myprint (DEBUG_LEVEL0,   progname + "KeyError in cfglist_akt, check values!")   


# nun wurde alle 5 Pins geholt, diese Instanz verwendet genau einen der Pins in der Liste Pins2
        self.mypin=self.Pins2[self.nummer]        # hole Pin NUmmer 
        GPIO.setup(self.mypin, GPIO.OUT)
 #       GPIO.output(self.mypin, True)
        self.myprint (DEBUG_LEVEL3,   progname + "aktor_init dose:{}, using GPIO:{}".format (self.dosennummer, self.mypin))
   
        self.errorcode=0    # init aktor ok

#-------------------------------------------
# __repr__ function Aktor_1
# 
    def __repr__ (self):

        rep = "Aktor_1 (Für Dose"  + str(self.dosennummer) + "," + self.action_type  + ")"
        return (rep)


#-------------Terminate Action PArt ---------------------------------------
# cleanup GPIO PIns
#------------------------------------------------------------------------
    def __del__(self):
        self.myprint (DEBUG_LEVEL2,   progname + "del called")
        
        if self.errorcode == 0:
            GPIO.cleanup(self.mypin)  # cleanup GPIO Pins


# ***** Function zum setzen GPIO *********************
    def schalten(self,einaus, debug_level_mod):
        global GPIO
  
        self.myprint (debug_level_mod,   progname + "schalten called: Gpio:{} [{}]".format (self.mypin, OFFON[einaus]))
#
        if einaus== 1:
            GPIO.output(self.mypin, True)         # dosen muss minus 1 sein wegen List index Dosen
        else:
            GPIO.output(self.mypin, False)

        return (0)                  # return code immer null
   
# ************************************************** 		


#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swc_aktor_1.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
