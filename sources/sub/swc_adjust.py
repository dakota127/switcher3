#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class calcAdjust 
#   
#   Diese Class impmentiert das pyhsische Schalten der Dosen 
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
import sys
import time
from time import sleep
from datetime import date, datetime, timedelta
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.myconfig import ConfigRead


DEBUG_LEVEL0=0                      
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

#------------
# -------------------------------------------------------------------------
FAKTOR = 0.17               # <------------------ FAKTOR für Berechnung ---------------
#-------------------------------------------------------------------------------------

progname = "CalcAdjust "
configfile_name = "swconfig.ini"
config_section = "sequencer"                # look up values in this section

changed = False

# Configdictionary
# Python dictionary for config values
# key-value pairs
# values are default values, the will not be changed if key not found in configfile 
#   Struktur (Dict) der Daten, die aus dem Configfile swconfig.ini gelesen werden
# s  hier die defaultwerte der 'variablen'
cfglist_seq = {
        "ctrl_file"             : "test_1",
        "adjust_needed"         : 1,
        "evening_start_limit"   : 23.00,
        "evening_ontime"        : 15,
        "morning_start_limit"   : 04.00,
        "morning_ontime"        : 30,
        "faktor"                : 17
}

#----------------------------------------------------
# Class Definition Aktor, erbt vom MyPrint
#----------------------------------------------------
class CalcAdjust (MyPrint):
    ' klasse CalcAdjust '

    
    def __init__(self, debug_in, all_weeks):  # Init Funktion

        self.myprint (DEBUG_LEVEL2,  progname + "CalcAdust_init called")

        self.debug = debug_in
        self.weeks = all_weeks  
       
        self.evening_start_limit = 0
        self.morning_start_limit = 0
        self.evening_ontime = 0
        self.morning_ontime = 0
        self.counter = 0
        self.faktor = FAKTOR


        self.myconfig = ConfigRead(debug_level = self.debug)     # Create Instance of the ConfigRead Class


    # we use the configfile given by switcher, could also use our own
        ret = self.myconfig.config_read (configfile_name ,config_section, cfglist_seq)  # call method config_read()
        self.myprint (DEBUG_LEVEL1, progname + "config_read() returnvalue: {}".format (ret))	# für log und debug
 
        self.myprint (DEBUG_LEVEL3, progname + "Configdictionary after reading:")
        if (self.debug > 2):
            for x in cfglist_seq:
                print ("{} : {}".format (x, cfglist_seq[x]))

    #    print (self.evening_start_limit)
    #    print (self.morning_start_limit )
        try:
            hhmm_s = cfglist_seq ["evening_start_limit"].split(".")
            hhmm_e = cfglist_seq ["morning_start_limit"].split(".")
            self.evening_ontime = int(cfglist_seq ["evening_ontime"])
            self.morning_ontime = int(cfglist_seq ["morning_ontime"])
            self.faktor = int(cfglist_seq ["faktor"]) / 100
        except KeyError :
            myprint.myprint (DEBUG_LEVEL0, progname + "KeyError in cfglist_seq, check values!")   


    #    print (hhmm_s)
    #    print (hhmm_e)
        self.evening_start_limit = (60 * int(hhmm_s[0])) + int(hhmm_s[1])       # minuten des Tages
        self.morning_start_limit  =   (60 * int(hhmm_e[0])) + int(hhmm_e[1])       # minuten des Tages
        self.myprint (DEBUG_LEVEL0, progname + "evstart:{} evon:{} mostart:{} moon:{} faktor:{}".format(self.evening_start_limit, \
                                                        self.evening_ontime,  \
                                                        self.morning_start_limit,  \
                                                        self.morning_ontime ,   \
                                                        self.faktor))


#-------------------------------------------
    # __repr__ function MySequencer
    # 
    def __repr__ (self):

        
        rep = "CalcAdjust, + evstart:{} evon:{} mostart:{} moon:{}".format(self.evening_start_limit, \
                                                        self.evening_ontime,  \
                                                        self.morning_start_limit,  \
                                                        self.morning_ontime )
        return (rep)

#  ---------------------------------------------------------------------------------------
#--Private  Funktion convert time  given ist switchtime in minutes of the day
#  ---------------------------------------------------------------------------------------
    def _convTime(self, min_in):
          
        c = min_in % 60         # c reminder is minutes  
        b = (min_in - c) // 60  # calc hour of the day
      
        f = str(c)
        e = str(b)
        if c < 10: f = "0" + str(c)
        if b < 10: e = "0" + str(b)
        return (e + "." + f)        # format "hh.mm"


#---------------------------------------------------------------------------------
# Private function calculate minutes based on week of yer
#---------------------------------------------------------------------------------
    def _calc_base (self, weeks):


        self.myprint (DEBUG_LEVEL3, "--> _calc_base called, weeks:{}".format(weeks))
        if weeks == 0:              

            today = datetime.now()
            week = int(today.strftime("%V"))    # use %V with Python 3.6 !! 
                                                # see https://bugs.python.org/issue12006
            self.weekyear = week

        else:
            self.weekyear = weeks

        self.adjust_time = int(abs( 60 * ((self.weekyear - 27) * (self.faktor)) ))  # number of minutes we need to adjust, based on week of the year

        #  evening and morning limits (hour/min and ontime)
        #  only adjust actions that are outside this boundary

      
        before_midnight = 1439          # shortly before midnigt (minutes of day)
      
        self.myprint (DEBUG_LEVEL3, progname + "Week des Jahres:{} ,adjust minutes:{}".format(self.weekyear,self.adjust_time))  
        self.myprint (DEBUG_LEVEL3, progname + "Evening:{}/{},Morning: {}/{}".format(  \
                                        self.evening_start_limit,   \
                                        self.evening_ontime, \
                                        self.morning_start_limit,  \
                                        self.morning_ontime))  

        return (self.weekyear, self.adjust_time)


#--------------------------------------------
# Public Function calc_adjust 
#--------------------------------------------
    def calc_adjusttime (self, action, week):

    #----------------------------------------------------------
    #   Eine Aktion sieht so aus:
    #   Element action = ("HH.MM", Zeit in Min, Dauer in Min, "HH.MM", Dose, ON/OFF)
    #   elemente:
    #   erstes "HH.MM" element ist ev. korrigierte Schaltezeit
    #   selbe Schaltzeit aner in Minuten des Tages
    #   Dauer eingeschaltet in Minuten
    #   zweites "HH.MM" element ist originale Schaltzeit
    #   Dosennummer
    #   1 = einschalten
    #   0 = ausschalten
    #-------------------------------------------------------------
       
        self.myprint (DEBUG_LEVEL3, progname + "action in:       {}".format(action))
        if week > 0:                                # >0 means = only calculate minutes, do nothing more...
            week,minutes = self._calc_base (week)
            return (action, minutes)

        week,minutes = self._calc_base (week)

        changed = False
        evening_valid = False
        morning_valid = False
    
        # is action am Abend und zwischen 18'00 Uhr und dem Abend-Grenzwert (evening_start_limit) ?
        # und ist ontime länger als evening_ontime ?
        if (action[1] < self.evening_start_limit) and (action[1] > 1080) and (action[2] > self.evening_ontime):
            evening_valid = True                    # yes must be adjusted
            self.myprint (DEBUG_LEVEL3, "\t" + progname + "is valid evening action")

        # is action am Morgen und zwischen dem Morgen-Grenzwert und 6 Uhr Morgens ? 
        # # und ist ontime länger als morning_ontime ?   
        if (action[1] > self.morning_start_limit) and (action[1] < 360) and (action[2] > self.morning_ontime): 
            morning_valid = True                   # yes must be adjusted
            self.myprint (DEBUG_LEVEL3, "\t" + progname + "is valid morning action")

        if evening_valid:
            action[1] = action[1] - minutes                           # adjust switch on time (minutes)
            action [0] = self._convTime(action[1])                       # adjust switch on time (hh.mm)
            changed = True
            self.myprint (DEBUG_LEVEL3, "\t" + progname + "new evening action:{}".format (action))
            
        if morning_valid:
            action[1] = action[1] + minutes    # adjust switch on time (minutes)
            action [0] = self._convTime(action[1])       # adjust switch on time (hh.mm)
            changed = True
            self.myprint (DEBUG_LEVEL3, "\t" + progname + "new morning action:{}".format (action))  
   
        if changed:
            self.counter = self.counter + 1
        #    self.myprint (DEBUG_LEVEL1, progname + "modified action: {}".format (action))
            pass
    # -- process the action given as parameter

        return (action, minutes)



#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swc_adjust.py. ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
