#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class Aktor_4
#   
#   Diese Class impmentiert das pyhsische Schalten der Dosen 
#
#   diese Class erbt von der MyPrint Class
#
#   Version für Funksteckdosen mit Handsender - wie Switcher Version 1 Peter
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
        
DEBUG_LEVEL1=0                     
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

config_section = "aktor_4"
progname = "swc_aktor4 "

OFFON = ['AUS','EIN']

# dict values from config file, Abschnitt Aktor_4
cfglist_akt = {      
        "gpio_1"    : 4,
        "gpio_2"    : 22,
        "gpio_3"    : 18,
        "gpio_4"    : 25,
        "gpio_5"    : 23,
        "gpio_6"    : 24,
}

#----------------------------------------------------
# Class Definition Aktor, erbt vom MyPrint
#----------------------------------------------------
class Aktor_4 (MyPrint):
    ' klasse aktor '
    aktorzahler=0               # Class Variable
    WAIT_NACH_SENDEN = 1.5      
    action_type=""                     
# define GPIO signals to use for sending signals
# and the mapping to signals -D and On/Off

# index:    0: not used
#            1: pin dose 1
#            2: pin dose 2
#            3: pin dose 4
#            4: pin dose 4
#            5: pin einschalten
#            6: pin ausschalten
            
    Pins=[0,4, 22,18,25]
    Pins_ein_aus=[23,24]

    def __init__(self, dosennummer,debug_in, config_filename_in):  # Init Funktion
        self.errorcode = 8
        self.nummer = Aktor_4.aktorzahler
        # configfile not used here ----
        self.debug=debug_in
        self.dosennummer=dosennummer            # arbeite für diese Dose (1 bis n)
        GPIO.setmode (GPIO.BCM)
        rev=GPIO.RPI_REVISION
        GPIO.setwarnings(False)             # juni2018 ist neu hier, war in gpio_setup()

        for i in range(1,len(Aktor_4.Pins)):
            GPIO.setup(Aktor_4.Pins[i], GPIO.OUT)
        
        for i in range(len(Aktor_4.Pins_ein_aus)):
            GPIO.setup(Aktor_4.Pins_ein_aus[i], GPIO.OUT)
        
        Aktor_4.action_type="Funk-OLD"     # welche art Schalten ist dies hier
        
        self.myprint (DEBUG_LEVEL2,  progname + "aktor_init called fuer Dose:{}".format (self.dosennummer))
        Aktor_4.aktorzahler +=1            # erhögen aktorzähler
        self.errorcode = 0          # aktor init ok

#-------------------------------------------
# __repr__ function Aktor_4
# 
    def __repr__ (self):

        rep = "Aktor_4 (Für Dose" + str(self.dosennummer) + "," + self.action_type  + ")"
        return (rep)


#-------------Terminate Action PArt ---------------------------------------
# cleanup GPIO PIns
#------------------------------------------------------------------------
    def __del__(self):
        self.myprint (DEBUG_LEVEL3,  progname + "del called")

        if self.errorcode == 0:
            for i in range(1,len(Aktor_4.Pins)):
                GPIO.cleanup(Aktor_4.Pins[i])
    


# ***** Function zum setzen GPIO *********************
    def schalten(self,einaus, debug_level_mod):
        global GPIO
        self.what=1
        self.myprint (debug_level_mod,  progname + "dose{} schalten called Gpio:{} [{}]".format (self.dosennummer, Aktor_4.Pins[self.dosennummer],OFFON[einaus]))
#
# parameter what indicates: 1: sender für waittime_senden einschalten und danch wieder ausschalten
#                           0: sender nur ausschalten (nötig bei Abbruch des programms durch ctrl-c)
        if self.what:				# what=1 says: do both
            GPIO.output(Aktor_4.Pins[self.dosennummer], True)
            GPIO.output(Aktor_4.Pins_ein_aus[einaus], True)
            time.sleep(Aktor_4.WAIT_NACH_SENDEN)
    # senden wieder ausschalten    
        GPIO.output(Aktor_4.Pins[self.dosennummer], False)
        GPIO.output(Aktor_4.Pins_ein_aus[einaus], False)

        time.sleep(Aktor_4.WAIT_NACH_SENDEN)     # korrektur habi (give transmitter time to settle down)

        return (0)                  # return code immer null
   
# ************************************************** 		


#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swc_aktor_4.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
