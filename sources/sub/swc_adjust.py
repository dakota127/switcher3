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


progname = "swc_adjust "
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
        "faktor"                : 17,
        "daylight_saving"       : 1,
        "spring_date"           : 31.03,    
        "fall_date"             : 31.10
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
        self.dayofyear = 0
        self.weekyear = 0
        self.adjust_time_min = 0    # in minutes
        self.today = 0
        self.do_adjustTime = 0                  # adjust times normal
        self.do_adjustDaylight_saving = 0       # adjust daylight saving time
        self.sommer_winter = "S"                # Sommer oder Winter (daylight Saving)
        self.evening_start_limit = 0
        self.morning_start_limit = 0
        self.evening_ontime = 0
        self.morning_ontime = 0
        self.counter = 0
        self.spring_datef = 0
        self.fall_datef = 0
        self.spring_day = 0
        self.fall_day = 0
        self.daylight_saving_minutes = 0         # anzahl minuten anpassung im Sommer (ZERO)

        self.faktor = 0


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
            self.do_adjustTime = int(cfglist_seq ["adjust_needed"])    
            self.do_adjustDaylight_saving = int(cfglist_seq ["daylight_saving"])
            if self.do_adjustDaylight_saving == 0: self.sommer_winter = "n.a"

            
            hhmm_s = cfglist_seq ["evening_start_limit"].split(".")
            hhmm_e = cfglist_seq ["morning_start_limit"].split(".")
            self.evening_ontime = int(cfglist_seq ["evening_ontime"])
            self.morning_ontime = int(cfglist_seq ["morning_ontime"])
            self.faktor = int(cfglist_seq ["faktor"]) / 100

            self.spring_datef = cfglist_seq ["spring_date"].split(".")
            self.fall_datef = cfglist_seq ["fall_date"].split(".")

   #         print ("===========================================")
   #         print (self.spring_datef[0] + "-" +  self.spring_datef[1])
   #         print (self.fall_datef[0] + "-" +  self.fall_datef[1])
    

        except KeyError :
            myprint.myprint (DEBUG_LEVEL0, progname + "KeyError in cfglist_seq, check values!")   

        self.today = datetime.now()

        self.dayofyear = int(self.today.strftime("%j"))      # tag des Jahres ermitteln 


    #    print (hhmm_s)
    #    print (hhmm_e)
        self.evening_start_limit = (60 * int(hhmm_s[0])) + int(hhmm_s[1])       # minuten des Tages
        self.morning_start_limit  =   (60 * int(hhmm_e[0])) + int(hhmm_e[1])       # minuten des Tages
        self.myprint (DEBUG_LEVEL1, progname + "evstart:{} evon:{} mostart:{} moon:{} faktor:{}".format(self.evening_start_limit, \
                                                        self.evening_ontime,  \
                                                        self.morning_start_limit,  \
                                                        self.morning_ontime ,   \
                                                        self.faktor))


#-------------------------------------------
    # __repr__ function MySequencer
    # 
    def __repr__ (self):

        
        rep = "CalcAdjust, evstart:{} evon:{} mostart:{} moon:{}".format(self.evening_start_limit, \
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
# Privat function adjust_init: calculate minutes to adjust based on week of year
# also berücksichtige SommerWinterzeit, wenn verlangt
#---------------------------------------------------------------------------------
    def adjust_init (self, weeks):

        self.today = datetime.now()                             
        self.dayofyear = int(self.today.strftime("%j"))      # tag des Jahres ermitteln 

        self.myprint (DEBUG_LEVEL2, progname + "adjust_init called, weeks:{}".format(weeks))
        if weeks == 0:              

            week = int(self.today.strftime("%V"))    # use %V with Python 3.6 !! 
                                                # see https://bugs.python.org/issue12006
            self.weekyear = week

        else:
            self.weekyear = weeks

        # ajustierung der Schaltzeiten verlangt ?
        if self.do_adjustTime == 1:       # 1 = verlangt
            self.adjust_time_min = int(abs( 60 * ((self.weekyear - 27) * (self.faktor)) ))  # number of minutes we need to adjust, based on week of the year
        else:
            self.adjust_time_min = 0     # nicht verlangt, also 0 minuten

        # nun noch Sommer-Winterzeit berücksichtigen, falls verlangt im Config File.
        # Alle Schaltzeiten sind im XML File für den Sommer
        # wenn verlangt, ist also im Winter 60 Minuten zur Adjust Zeit hinzufügen
        
        # zuerst feststellen, ob Sommer oder Winter, im Config file ist der Tag des Wechsels im Frühling und im Herbst definiert.
        
        # aktueller Monat und Tag des Monats
        month = int(self.today.strftime("%-m"))    # use with Python 3.6 !! 
        day_month = int(self.today.strftime("%-d")) 
        year = int(self.today.strftime("%-Y")) 

        spring = datetime(year, int(self.spring_datef[1]), int(self.spring_datef[0]))       # datuemer aus KOnfig File
        fall = datetime(year, int(self.fall_datef[1]), int(self.fall_datef[0]))             # datuemer aus KOnfig File
       
        self.spring_day = int(spring.strftime("%j")) 
        self.fall_day =   int(fall.strftime("%j") )

     
        # Sind wir Sommer oder Winterzeit ?
        self.daylight_saving_minutes = 0            # in Sommer zusätzlich 0 min früher 
       
        # berücksichtigen Sommer/Winterzeit verlangt ?
        if self.do_adjustDaylight_saving == 1:       # 1 = verlangt
            self.myprint (DEBUG_LEVEL1, progname + "Daylight-Saving verlangt")
            # entscheiden, ab das aktuelle Datum im Sommer oder Winterhabljahr liegt.
            self.sommer_winter = "S"                # nehme default an Sommer

       
            # im Winter schieben wir Zeit um nochmals + 60 Minuten
            if (self.dayofyear > self.spring_day) and (self.dayofyear <= self.fall_day):  # Sommerzeit
                self.myprint (DEBUG_LEVEL0, progname + "Sommerzeit, TagJahr:{}/FallDay:{}/SpringDay:{}".format (self.dayofyear,self.fall_day, self.spring_day ))    
        
            else:
                self.daylight_saving_minutes = 60            # in Winterzeit zusätzlich 60 min früher 
                self.sommer_winter = "W"
                self.myprint (DEBUG_LEVEL0, progname + "Winterzeit, TagJahr:{}/FallDay:{}/SpringDay:{}".format (self.dayofyear,self.fall_day, self.spring_day ))   
           
        else:
            self.myprint (DEBUG_LEVEL1, progname + "Daylight Saving nicht verlangt")

        #  evening and morning limits (hour/min and ontime)
        #  only adjust actions that are outside this boundary

        before_midnight = 1439          # shortly before midnigt (minutes of day)



        self.myprint (DEBUG_LEVEL0, progname + "Week des Jahres:{} ,adjust minutes:{} ,adjust minutes(total):{}".format(self.weekyear,self.adjust_time_min,(self.adjust_time_min+self.daylight_saving_minutes)))  
        self.myprint (DEBUG_LEVEL3, progname + "Evening:{}/{},Morning: {}/{}".format(  \
                                        self.evening_start_limit,   \
                                        self.evening_ontime, \
                                        self.morning_start_limit,  \
                                        self.morning_ontime))  
    


        return (self.sommer_winter, self.adjust_time_min + self.daylight_saving_minutes,self.faktor )


#--------------------------------------------
# Public Function calc_adjust 
#--------------------------------------------
    def adjust_time (self, action, week):

    # wird aufgerufen, wenn Schaltzeiten zu modifizieren sind, dies kann sein:
    #
    # >  Anpassung an veränderten Sonnenuntergang zwischen den Saisons (Schaltzeiten sind für den Sommer definiert und müssen nach 
    #   vorne angepasst werden, weil es im Herbst/Winter früher dunkel wird). Dies wird pro Woche des Jahres berechnet.
    # >  Anpassung Sommer/Winterzeit (in der Winterzeit werden Schaltzeiten generell um 60 Min nach vorne verschoben.)
    #
    # >  Die beiden Anpassungen können im Configfile unabhängig konfiguriert werden. Es um das Total der Ajustierungen ajustiert.
    #
    #   Input ist eine Aktion, welche folgende Struktur hat:
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
       
        self.myprint (DEBUG_LEVEL2, progname + "adjust_time called, week:{}, action in:{}".format(week,action))
        
        # dies ist nur für Ausgabe, nicht sehr wichtig hier
        if week > 0:                                # >0 means = only calculate minutes, do nothing more...
            self.adjust_init (week)
            self.myprint (DEBUG_LEVEL2, progname + "adjust_time min:{}".format(self.adjust_time_min + self.daylight_saving_minutes))
            return (action, self.adjust_time_min + self.daylight_saving_minutes)

       # self.adjust_init (week)        nicht mehr nötig, Nov 21

        # nun art der ajustierung ermitteln:
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
            action[1] = action[1] - self.adjust_time_min - self.daylight_saving_minutes    # adjust switch on time (minutes)
            action [0] = self._convTime(action[1])                       # adjust switch on time (hh.mm)
            changed = True
            self.myprint (DEBUG_LEVEL3, "\t" + progname + "new evening action:{}".format (action))
            
        if morning_valid:
            action[1] = action[1] + self.adjust_time_min + self.daylight_saving_minutes  # adjust switch on time (minutes)
            action [0] = self._convTime(action[1])       # adjust switch on time (hh.mm)
            changed = True
            self.myprint (DEBUG_LEVEL3, "\t" + progname + "new morning action:{}".format (action))  
   
        if changed:
            self.counter = self.counter + 1
        #    self.myprint (DEBUG_LEVEL1, progname + "modified action: {}".format (action))
            pass
    # -- process the action given as parameter

        self.myprint (DEBUG_LEVEL2, progname + "adjust_time: new Action2:{}".format(action))
        # gebe angepasste Aktionsstruktur zurück
        return (action, self.adjust_time_min + self.daylight_saving_minutes)



#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swc_adjust.py. ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
