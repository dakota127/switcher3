#!/usr/bin/python
# coding: utf-8
# ***********************************************************
# 	Class Sequencer 
#   
#   Diese Class kapselt die Herstellung von Events
#   Es gibt drei Arten von Events:
#       Action Events, betreffen Ein/Ausschalten von Dosen zu bestmmten Zeitpunkten
#       Time of Day Events, wie Mitternacht, TimeNow
#       Update Event to set Room ID into the device instances (only done once)

#   diese Class erbt von der MyPrint Class
#   diese Class benutzt die Class ConfigRead
#   diese Class benutzt die Class ActionList, welche einen Liste der Aktionen führt
#   
#   Feb 2021 
#************************************************
#
import atexit
import time
import locale
import threading

from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.myconfig import ConfigRead
import os
from datetime import date, datetime, timedelta
import threading
from sub.swc_actionlist import ActionList
from sub.swc_adjust import CalcAdjust
from operator import itemgetter
# from sub.configread_dosen import read_dosenconfig
from sub.swc_dosconf import SWDos_conf          # classe anzahl Dosen in swdosen.ini File


DEBUG_LEVEL0 = 0                      
DEBUG_LEVEL1 = 1
DEBUG_LEVEL2 = 2
DEBUG_LEVEL3 = 3

configfile_name = "swconfig.ini"
config_section = "sequencer"                # look up values in this section
progname = "swc_sequencer "
dosenconfig = "swdosen.ini"
hhmm_tag = 0
status_currtime = 0
time_old = 0

JANEIN=["Nein","Ja"]
ONOFF={1:'EIN', 0:'AUS'}     
wochentage=["Sonntag","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag"]
reset_man=["Nie","Mitternacht"]
SLEEPTIME=2			            # default sleeptime normaler Lauf
SLEEPTIME_DONE = 30             # sleeptime vor Mitternacht (alle Aktionen gemacht)
# variablen, die für die Status Abfrage geführt/verwendet werden

swdosconf = None            # object (Instanz von Klasse)



# parameter for callback from sequencer class
# values Parmameter1
ACTION_EVENT         = 1
ACTION_EVENT_FRAME2         = 2
TIME_OFDAY_EVENT            = 3  
UPDATE_EVENT                = 4

# values Parmameter2
MIDNIGHT                = 1  
NOON                    = 2
ACTUAL_NOW              = 3
NOTUSED                 = 0
# values Parmameter3 is device Number
# values Parmameter4 is
DEVON               = 1
DEVOFF              = 0 
# values Parmameter5 is time in format "hh.mm"

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


#--------------------------------------------------------------------
# vom Parser werden 3 Listen erstellt aufgrund der Daten im XML File

# list_tage[] ist Liste über alle Aktionen pro Wochentag, chronologisch
# ein entry dieser Liste ist eine liste aus 3 elementen: ["hh.mm", devicenummer, 0/1]
# dise Liste wird von Sequencer abgearbeitet
# self.list_tage= [ [] for z in range (1)]
# 
# list_device:  Liste über alle Tage, pro Tag alle devices und pro device alle aktionen 
# ein entry dieser Liste ist eine liste aus 2 elementen: ["hh.mm", 0/1]
#   WICHTIG:    diese Liste wird nur aufgebaut, damit swlist_action eine Liste über alle Dosen erstellen kann.<<-----------------
#               switcher3.py braucht diese Liste nicht.
# self.list_device= [ [] for z in range (1)]                                    

# Lisre aller Namen der Zimmer
# self.list_zimmer =[]
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
#-------------------------------------------------------------------


class MySequencer(threading.Thread, MyPrint):
    """Sequencer Class: knows about the switch_actions for the day, keeps track of time and issues
        events of different kinds"""

    def __init__(self, debug_in, path_in, conf, callback1 ) :
        """Initialize the 'thing'."""
        super().__init__()
        self.debug = debug_in
        self.path = path_in             # path switcher main 
        self.callback = callback1
        self.configfile = conf          # full pfad  switcher config file
        self.myprint (DEBUG_LEVEL1, "\t" + progname + "_init called")
        self.myconfig = None
        self.anz_devices=0
        self.start_time = datetime.now()       # setze start zeit 
        # --------- 3 Lists are built bei the parser, see above for description
        self.list_tage  = [ [] for z in range (7)]          # list has 7 members: one for every day of the week
        self.list_device= [ [] for z in range (7)]          # list has 7 members: one for every day of the week                               
        self.list_zimmer =[]                                # list of all rooms
        self.list_tage_new = None
        self.list_device_new = None
        # ------------------------
        self.list_aktionen_past =[]
        self.list_aktionen_zukunft =[] 
        self.total_aktionen_protag = []
        self.status_currtime=""              # fuer Statusanzeige
        self.do_adjustTime = 0                  # 1: adjust times, 0: nichts ajustieren
        self.do_adjustDaylight_saving = 0       # 1 : adjust daylight saving time, 0: nichts machen
        self.term_verlangt = 0
    
        self.daylight_saving_season = ""        # S oder W   (Sommer /Winter)
        self.maxchar_zimmer = 0
        self.adjust_time = 0
        self.anz_dosen_config = 0
        self.anz_dosen_xml = 0
        self.file_id = ""
        self.start_tag = 0  # mit diesem Wochentag starten wir (wird später auf aktuelen Tag gesetzt nach Start)

    
        self.weekyear = ""
        
        self.wochentag = 0
        self.current_action = 0
        # variables for status
        self.status_anzactions_done=0             # fuer Statusanzeige Anzahl Actions durchgefuehrt seit Start
        self.status_nextaction=[99,""]       # fuer Statusanzeige was wird als naechstes  geschaltet, dosennummer und string                               # 99 ist init
        self.status_lastaction=[99,"none"]   # fuer Statusanzeige was wurde zuletzt geschaltet, dosennummer und string                               # 99 ist init
        self.status_waitfor=""               # fuer Statusanzeige Zeit der noechsten, in der Zukunft liegenden Aktion

        self._do_setup()            # do setup sequencer
        
        self.actioncalc = CalcAdjust(self.debug, 0 )     # instanz von CalcAdjust erstellen 
        
        self.myprint (DEBUG_LEVEL0 ,"\t" + progname +  "object created: {}".format(self.actioncalc))
        time.sleep(.1)       # initial wait 
        self.myprint (DEBUG_LEVEL1, "\t" + progname + "_init done")


    #-------------------------------------------
    # __repr__ function MySequencer
    # 
    def __repr__ (self):
        
        rep = "MySequencer ( )"
        return (rep)



    #  --- Funktion zum Erstellen von zwei Listen ----------------
    #		a: Liste aller vergangenen 	Aktionen eines bestimmten Tages
    #		b: Liste aller zukünfigen 	Aktionen eines bestimmten Tages
    #		basierend auf aktueller Zeit
    #       nur dosen nehmen, die kleiner/gleic max_dose sind
    #  ---------------------------------------------------------------------------------------
    def _aktionen_pro_tag (self, liste, weekday,  max_dose):

        self.myprint (DEBUG_LEVEL2,   "\t" + progname + "aktionen_pro_tag() called, wochentag: {}".format(self.wochentag))
        self.myprint (DEBUG_LEVEL2,   "\t" + progname + "sammle alle aktionen pro Tag fuer Dosen kleiner/gleich: {}".format(max_dose))
        hhmm_tag = [datetime.now().strftime("%H.%M"),datetime.today().strftime("%w")]    # aktuelle Zeit holen
      #     --> wir nehmen nur jenen Aktionen, die für die definierte Anzahl Dosen gelten
      
      #  print (hhmm_tag)
        new_list_vergangen = []
        new_list_zukunft =[]

      #  print (liste)
        for n in liste[weekday]:                      # loop über alle Aktionen dieses Tages
            self.myprint (DEBUG_LEVEL3,   "\t" + progname + "extrakt aktion: {}".format(n))				# ist aktio
        
            if (n[4] <= max_dose):                      # nehme nur jene die kleiner/glich sind
                if hhmm_tag[0] > n[0]:					# hhmm_tag[0] sind Stunden.Minuten, check Actions times to current time
                    new_list_vergangen.append(n)		# addiere zur Liste vergangene Aktionen
##                    print ("vergangen: {}".format(n))
                else:								
                    new_list_zukunft.append(n)			# addiere zur Liste der zukünftigen Aktionen
##                    print ("zukunft: {}".format(n))


        return (new_list_vergangen, new_list_zukunft)	# gebe beide Listen zurück

#  ---------------------------------------------------------------------------------------
#  -- Funktion: warten bis der nächste wochentag wirklich eintrifft -
#  ---------------------------------------------------------------------------------------
    def warte_bis_tag_da(self,weekday):
   #
        self.myprint (DEBUG_LEVEL0,   "\t" + progname + "warte_bis_tag_da() called. Es ist tag: {}".format(weekday))

        # loop bis condition is erfüllt, alo neuer Tag ist gekommen...
        while True:
            hhmm_tag = [datetime.now().strftime("%H.%M"),datetime.today().strftime("%w")]  # aktuelle Zeit holen
            self.status_currtime = hhmm_tag[0]               # fuer status request ===============  juni2018

            wochentag_neu = int(hhmm_tag[1])            # get new weekday
            if wochentag_neu != weekday:              #  ist neuer Tag ?
                self.myprint (DEBUG_LEVEL0,   "\t" + progname + "Neuer Tag ist da: {}".format(wochentag_neu))
                return (wochentag_neu)                 # we have reached a new day hurray

            # no new day yet, continue...    
            time.sleep(SLEEPTIME_DONE)
            self.myprint (DEBUG_LEVEL1,   "\t" + progname + "Timemarching warte auf neuen tag, immer noch tag {} / {}".format(hhmm_tag[1], hhmm_tag[0]))

            self.do_stuff_regular()              # do regular stuff

            if  self.term_verlangt==1:  
                self.myprint (DEBUG_LEVEL2,   "\t" + progname + "wartend auf neuen Tag finds self.term_verlangt=1")
                return (5)                              # gebe irgendwas zurück, der form halber    



    #  --------------------------------------------------------------------------------------- 
    #  --Funktion: warten auf die Zeit der nächsten Aktion 
    #  ---------------------------------------------------------------------------------------
    def warte_bis_zeit_da(self,zeit):

        hhmm_tag = [datetime.now().strftime("%H.%M"),datetime.today().strftime("%w")]    # aktuelle Zeit holen
        self.myprint (DEBUG_LEVEL2,   "\t" + progname + "warte_bis_zeit_da() called. naechste Aktion um: {}".format(zeit))

        while True: 
            if hhmm_tag[0] >= zeit:	            #	pruefe ob jetzt die Zeit da ist fuer aktuelle Aktion		
                return
                self.myprint (DEBUG_LEVEL1,   "\t" + progname + "neue Zeit ist da: {}".format(self.aktion[0]))
                return
            time.sleep(SLEEPTIME_DONE)
            hhmm_tag = [datetime.now().strftime("%H.%M"),datetime.today().strftime("%w")]    # aktuelle Zeit holen HH.MM
            self.myprint (DEBUG_LEVEL2,   "\t" + progname + "Timemarching warte auf zeit {}, jetzt ist {}".format (zeit, hhmm_tag[0]))
            self.status_currtime = hhmm_tag[0]               # fuer status request ===============  juni2018

            self.do_stuff_regular()                          # mache diese sachen regelmässig...

            if  (self.term_verlangt == 1):  
                self.myprint (DEBUG_LEVEL2,   "\t" + progname + "wartend auf neue zeit finds self.term_verlangt=1")
                break    
                
            pass
    # -------------------------------------------------      
    
    #--------------------------------------------------
    # actionList
    #-------------------------------------------------

    
    
    #---------------------------------------------------------------
    #------ Funktion do_stuff regular
    #--------------------------------------------------------------- 
    def do_stuff_regular(self):
        return


    #  ---------------------------------------------------------------------------------------
    #------ Funktion adjust action times 
    # wird aufgerufen, wenn dies im config file verlangt ist
    #  ---------------------------------------------------------------------------------------
    def _adjust_switchtimes (self, list_in):

        self.myprint (DEBUG_LEVEL2, "\t" + progname + "_adjust_switchtimes called")
        
        self.today = datetime.now()
        self.weekyear = int(datetime.now().strftime("%V"))    # use %V with Python 3.6 !! 
                                                # see https://bugs.python.org/issue12006
     # wenn a) 
        # Anpassung der Schaltzeiten verlangt ist (im Configfile), 
        # oder b)
        # Berücksichtigung Sommer-Winterzeit verlangt ist,
        # so machen wir das hier 
        # wenn beides nicht verlangt ist, geben wir einfach die bestehende Liste zurück ohne Aenderung
    
        if (self.do_adjustTime == 0) and (self.do_adjustDaylight_saving == 0):             # Nov 21
            return (list_in)


        #  eines von beiden (oder beides) ist verlangt, also machen wir das hier
        # init der adjust routine, liefert woche des Jahres und total ajustierung in min zurück
        self.daylight_saving_season, self.adjust_time = self.actioncalc.adjust_init (0)               # init call

        #print ("++++++++++++++++++++++++")
        #print (self.daylight_saving_season)

        adjust_list_tag     = [ [] for z in range (7)]     # BIG Liste ueber alle Tage  

        #---------------------------------------------------------------------------
        # now let us iterate over all days and over all devices and over all actions per day  in list_in 
        for wochentag, tag in enumerate (list_in):            # loop über alle 8 Tage
        
        #   for tag in list_in:
        #        for device in tag:
            for action in tag:
                new_action = self.actioncalc.adjust_time (action , 0)      # adjust schalt zeit
               #   append the updated (or unchanged) action to the two lists
                adjust_list_tag [wochentag].append (new_action)

        # now we need to sort the day list according to action time
        for wochentag, tag in enumerate (adjust_list_tag):
            adjust_list_tag[wochentag].sort(key=itemgetter(1))


        if self.debug > 2:
            for wochentag, tag in enumerate (adjust_list_tag):
                print ("neue Liste (Tag_liste) tag: {}".format(wochentag))
                for aktion in adjust_list_tag[wochentag]:
                    print (aktion)            


        # finally we are done adjusting 
        self.myprint (DEBUG_LEVEL2, "\t\n" + progname + "_adjust_switchtimes ended")
    
        # wir geben eine neue Liste mit geänderten Aktionen zurück
        return (adjust_list_tag)


    #---------------------------------------------------------------
    #------ Funktion show_status
    #---------------------------------------------------------------
    def show_status(self):

        now_time = datetime.now()
     #   return ([   str(self.weekyear) + "/" + str(self.adjust_time), \
        return ([   self.do_adjustTime,              \
                    self.weekyear,                      \
                    self.adjust_time,                   \
                    self.file_id,                       \
                    wochentage[self.wochentag],         \
                    str(self.total_aktionen_protag),    \
                    str(self.status_anzactions_done),   \
                    self.status_waitfor,                \
                    self.status_nextaction[1],          \
                    self.status_lastaction[1],          \
                    self.anz_dosen_config,              \
                    self.start_time.strftime("%A, %d %B %Y : %H:%M:%S" ),    \
                    now_time.strftime("%A, %d %B %Y : %H:%M:%S" ),  \
                    now_time.strftime("%H:%M" ),  \
                    self.do_adjustDaylight_saving, \
                    self.daylight_saving_season    \
                    ])


    #---------------------------------------------------------------
    #------ Funktion RUn Sequencer
    #--------------------------------------------------------------- 
    def run(self):

        time.sleep(1)       # initial wait
        try:
            self.running()       # execute the sequencer
        except Exception:
            self.myprint_exc ("Sequencer: etwas Schlimmes ist passiert.... !")
        finally:
            pass
          #  print ("sequencer finally reached") 

        # terminate Thread by returning 
        return
    #---------------------------------------------------------------
    #------ Funktion running the Sequencer
    #--------------------------------------------------------------- 
    def running(self):
        self.myprint (DEBUG_LEVEL0, "\t" + progname + "now running ---->> Start Switching <<-----")

        self.myprint (DEBUG_LEVEL1,  "\t" + progname + "Anzahl Dosen konfiguriert in swdosen.ini: {}". format(self.anz_dosen_config))     

     #   print (self.list_zimmer)

   # hier beginnt run_switchter() ------------------------
        if self.debug: 
            time.sleep(1) 
      
        hhmm_tag = [datetime.now().strftime("%H.%M"),datetime.today().strftime("%w")]    # aktuelle Zeit holen
        self.myprint (DEBUG_LEVEL0,   "\t" + progname + "start switching. Zeit und Wochentag: {}".format(hhmm_tag))
    
        time_old = datetime.now()                           # fuer Zeitmessung

        self.start_tag = int(hhmm_tag[1])                        # heutiger wochentag, starte damit, loop bis tag 6


        self.list_tage_new = self._adjust_switchtimes (self.list_tage)              # adjust SCHALTZEITEN WENN NÖTIG

        
        # Nun extrahieren von vergangenen und zukünftigen Aktionen (gemessen an der Startzeit des Switchers) für den aktuellen Tag
        # aber nur für dosen kleiner/gleich der anzahl konfigurierten dosen !
        # entweder von bestehender oder von neuer Liste
        self.list_aktionen_past, self.list_aktionen_zukunft = self._aktionen_pro_tag (self.list_tage_new, self.start_tag , self.anz_dosen_config )
        
    
    # Vorbereitung ist nun fertig--------------------------------------------------------------------
    # nun haben wir also zwei Listen aller verlangten Aktionen des heutigen Tages, die müssen wir nun abarbeiten
    # Liste 1: alle Aktionen, die schon (gemessen an der aktuellen Zeit) in der Vergangenheit liegen
    # Liste 2: alle zukünftigen Aktionen des Tages
    #----------------------------------------------------------
    #   Eine Aktion sieht so aus (aus swactionlist.py kopiert)  :
    #   Element action = ("HH.MM", Zeit in Min, Dauer in Min, "HH.MM", Dose, ON/OFF)
    #   elemente:
    #   0: erstes "HH.MM" element ist ev. korrigierte Schaltezeit
    #   1: selbe Schaltzeit aber in Minuten des Tages
    #   2: Dauer eingeschaltet in Minuten
    #   3: zweites "HH.MM" element ist originale Schaltzeit (vor adjust)
    #   4: Dosennummer
    #   5: 1 = einschalten / 0 = ausschalten
    #-------------------------------------------------------------
    #
    # --  Zuerst die vergagenen Aktionen des Tages behandeln ---
    #     dies, falls der Switcher in Laufe des Tages gestartet wird  - damit Status der Dosen aktuell ist
    #     gibt es also nur bei Neustart innerhalb des Tages !!!
        self.myprint (DEBUG_LEVEL1,   "\t" + progname + "behandle vergangene aktionen, anzahl: {}".format(len(self.list_aktionen_past)))
        self.status_anzactions_done = 0                               # fuer statusanfrage
        
        # nur bei debug >1
        if (self.debug > 1):
            print (progname + "vergangene aktionen:")
            for akt in self.list_aktionen_past:    
                print (akt)  
        
        # alle vergangenen Aktionen des Tages schnell virtuell machen
        for self.aktion in self.list_aktionen_past:                   # liste der vergagnenen aktionen des tages
            dosennu = int(self.aktion[4])                              #xxx   device nummer
            ein_aus = int(self.aktion[5])                              # 1 = ON 0 = OFF

            # nur dosennummer kleiner als config behandeln -----
            # wir rufen den callback, dieser ist lokalisiert in der swHome Class
            # sie ruft dann die betreffende Doseninstanz zu schlaten auf.
            if dosennu <= self.anz_dosen_config:
                self.callback.handle_sequencer_event ( [   ACTION_EVENT, 
                                    NOTUSED, 
                                    dosennu, 
                                    ein_aus, 
                                    NOTUSED,
                                    NOTUSED,
                                    self.aktion[0],

                ])                      #   <<<<----schalte die Dose (virtuell)        uni2018   
       
                                                        # bei Funkschaltung wollen wir nicht so lanke funken, bis alles abgearbeitet ist      
            self.status_anzactions_done+=1                            # increment anzahl getaner self.aktionen                
            self.status_lastaction[1] = "{} Uhr, {} / {}".format (self.aktion[0],self.list_zimmer[self.aktion[4]-1], ONOFF[self.aktion[5]])
            self.status_lastaction[0] = self.aktion[4]

        #  nun haben wir die vergangenen Aktionen virtuell geschaltet - also bloss den internen Status gesetzt haben,
        #  muessen wir nun noch die Dosen gemaess diesen Stati wirklich schalten.
      
        #  wir teilen der swHome klasse mit, dass nun die Abarbeitung die aktuelle Zeit erreicht hat, also
        #  ein TIME_OF_Day event.
        self.callback.handle_sequencer_event ( [   TIME_OFDAY_EVENT, 
                            ACTUAL_NOW, 
                            NOTUSED, 
                            NOTUSED, 
                            NOTUSED,
                            NOTUSED,
                            self.status_currtime,
        ])                      #   <<<<----Time of day event    Time actual reached    uni2018     
        
        self.myprint (DEBUG_LEVEL0,   "\t" + progname + "vergangene aktionen sind erledigt")

# ---- Alle vergangenen Aktionen des Tages erledigt. Nun gehts ans Schalten..
    
#----------------------------------------------------------------------------    
#  ---- Main Loop -----------------------------------------------------------   
#   hier werden die restlichen Aktionen des Tages behandelt.
#
# posit: solange, falls kein Ctlr-C kommt
        self.term_verlangt = 0

        while True:                                     # MAIN-LOOP  run forever
                                                    # check termination from daemon - signalled via global variable    
            if  (self.term_verlangt == 1): break                 # break from main Loop
            self.myprint (DEBUG_LEVEL1,   "\t" + progname + "MAIN-LOOP: starte mit wochentag: {}".format(self.start_tag))
        
 # LOOP----------  Loop ueber alle Tage der Woche ab start_tag ---------------           
            for self.wochentag in range(self.start_tag, 7):
            
                self.total_aktionen_protag = len (self.list_aktionen_past) + len(self.list_aktionen_zukunft)   # total number of actions for current day
                if self.debug:  
                    self.myprint (DEBUG_LEVEL1,   "\t" + progname + "Arbeite an Wochentag: {} hat {} Aktionen, davon {} vergangene bereits erledigt".format( self.wochentag, self.total_aktionen_protag, len(self.list_aktionen_past)) )
                time.sleep(1)
                

                self.myprint (DEBUG_LEVEL1,   "\t" + progname + "behandle zukünftige aktionen, anzahl: {}".format(len(self.list_aktionen_zukunft)))

                if (self.debug > 2):
                    print (progname + "zukünftige aktionen:")
                    for akt in self.list_aktionen_zukunft:    
                        print (akt)  

#----- L2 ueber alle restlichen Actions eines Tages --------------------------------------------------
                self.current_action = None           # make empty 
                for x in range (len(self.list_aktionen_zukunft)):

         #       for self.aktion in self.list_aktionen_zukunft:       
            
                    self.current_action = self.list_aktionen_zukunft.pop(0)   # get the next action into current
                    self.status_nextaction[1] = "{} Uhr, {} / {}".format (self.current_action[0],self.list_zimmer[self.current_action[4]-1], ONOFF[self.current_action[5]])
                    self.status_nextaction[0] = self.current_action[4]    # dosennummer fuer status request ===============
                    self.status_waitfor = "{} Uhr".format(self.current_action[0])          # fuer status request  Zeit auf die wir warten als String===============
            
                    self.warte_bis_zeit_da (self.current_action[0])       # hierin wird gewartet, is die Zeit reif ist...
                               
# ++++++++ Hier wird geschaltet +++++++++++		
#  ++++++++	Fuehre Aktion aus (Ein oder Aus schalten einer Dose)  +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++		
                    self.myprint (DEBUG_LEVEL2,  "\t" + progname + "Schalten der Dose:{}  Zeit:{}/{}".format ( self.current_action[4], self.current_action[0], ONOFF[self.current_action[5]]  ))				                         
                    dosennu = int(self.current_action[4])
                    ein_aus = int(self.current_action[5])
                    self.callback.handle_sequencer_event ( [   ACTION_EVENT, 
                                        NOTUSED, 
                                        dosennu, 
                                        ein_aus, 
                                        NOTUSED,
                                        NOTUSED,
                                        self.current_action[0],
                    ])                      #   <<<<----schalte die Dose      
        
                    self.list_aktionen_past.append(self.current_action)          # add current (just done) action to past actions list

#                                  
#  ++++++++ Schalten  fertig ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
#  ++++++++++++++++++++++++++++

#  nun ss setzen für Statusanfrage
                    self.status_lastaction[1] = "{} Uhr,  {} / {}".format (self.current_action[0],self.list_zimmer[self.current_action[4]-1], ONOFF[self.current_action[5]])
                    self.status_lastaction[0] = self.current_action[4]
                    self.status_anzactions_done+=1                # increment anzahl getaner Aktionen                

                    time.sleep(SLEEPTIME)
                    if  self.term_verlangt==1:               # check in outer loop
                        self.myprint (DEBUG_LEVEL2,   "\t" + progname + "inner Loop finds self.term_verlangt=1")
                        break                       
                    self.current_action = None           # make empty  , no current action, all done
            
                     
                pass
        #-----  # hier kommt man, wenn alle Aktionen des aktuellen tages gemacht sind -----------------------------------------------       
            # Der Tag ist aber noch nichht vorbei...
                self.myprint (DEBUG_LEVEL0,  "\t" + progname + "Alle Aktionen gemacht für Tag %d, nun warten auf neuen Tag " % self.wochentag)
                time.sleep(SLEEPTIME)

#  
#   fuer aktuellen Tag gibt es nichts mehr zu tun.....
#   das  im Status angegeben werden - ueber den naechsten Tag wissen wir nichts
                if  self.term_verlangt == 1:  
                    self.myprint (DEBUG_LEVEL2,   "\t" + progname + "LOOP-1 finds self.term_verlangt=1")
                    break                                   # break loop ueber alle actions des Tages

        #wir warten auf den neuen Tag und es gibt keine Aktionen mehr fuer den aktuellen Tag
        #Daten ablegen fuer statusabfrage. Wir wissen noch nicht, welche Aktion dann im neuen Tag kommen wird
                self.status_waitfor = "Neuer Tag"                     
                self.status_nextaction[1] = "Vorlaeufig unbekannt"      
                self.status_nextaction[0] = 99                   # damit zimmer unbekannt gesetzt wird    
     
                # warten bis Tag wechselt
                self.wochentag = self.warte_bis_tag_da(self.wochentag)     # hierin wird gewartet, bis der neue tag kommt (mitternacht)

                if  self.term_verlangt == 1:  
                    self.myprint (DEBUG_LEVEL2,   "\t" + progname + "LOOP-1 finds self.term_verlangt=1")
                    break                                   # break loop ueber alle actions des Tages
                              
                # wenn neuer Tag da ist, werden die Aktionslisten dieses neuen Tages erstellt    
             
                self.list_aktionen_past, self.list_aktionen_zukunft = self._aktionen_pro_tag (self.list_tage_new, self.wochentag ,self.anz_dosen_config)
                self.status_anzactions_done = 0                       # anzahl getaner Aktionen pro Tag
                                   
                                                        # manuell im configfile: 0= forever, 1=nur bis Mitternacht)                                          
        
                self.myprint (DEBUG_LEVEL0,   "\t" + progname + "Neuer Tag, send midnight event")
                    
        
                self.callback.handle_sequencer_event ( [   TIME_OFDAY_EVENT, 
                                        MIDNIGHT, 
                                        NOTUSED, 
                                        NOTUSED, 
                                        NOTUSED,
                                        NOTUSED,
                                        "00.00",
                    ] )                      #   <<<<----Time of day event    midnight reached    uni2018     
                
            pass
         
# Ende L1-----------------------  alle Tage vorbei
    
        self.start_tag = 0           # fuer neuen durchlauf Main Loop , wir starten dann bei wochentag = 0 (Sonntag)
# Ende MLoop 
#------------------------------------
#  Diesein Loop wird nur beendet, wenn variable self.term_verlangt=1 ist oder
#  wenn Keyboard interrupt kommt, ctrl-c ----

        self.myprint (DEBUG_LEVEL1, "\t" + progname + "Main Loop beendet, wir kommen zum Ende")

    


#----------------------------------------------
# liefere 2 Listen: 
#       alle vergangenen aktionen des aktuellen Tages
#       alle zukünftigen aktieonen des aktuellen Tages
#---------------------------------------------

    def show_dayactions (self):

        past_list =["keine vergangenen Aktionen"]
        zuku_list = ["keine zukünftigen Aktionen"]


        for i in range (len(self.list_aktionen_past)):
            print ("dose: {}".format(self.list_aktionen_past[i][4]-1))                      # xxx
            past_list[i] = ("Zeit: {} ({}) {:3} Dose: {} {:15}".format (
                                        self.list_aktionen_past[i][0],                      \
                                        self.list_aktionen_past[i][3],                      \
                                        ONOFF[self.list_aktionen_past[i][5]],               \
                                        self.list_aktionen_past[i][4],                      \
                                        self.list_zimmer [self.list_aktionen_past[i][4]-1] )) 
        #    past_list[i] = self.list_aktionen_past[i][0]
            past_list.append("")

        if self.current_action != None:
            zuku_list[0] =  ("Zeit: {} ({}) {:3} Dose: {} {:15}".format(
                                        self.current_action[0],                  \
                                        self.current_action[3],                  \
                                        ONOFF[self.current_action [5]] ,          \
                                        self.current_action[4],                  \
                                        self.list_zimmer [self.current_action[4]-1] ))    
            zuku_list.append("")   

        for i in range (len(self.list_aktionen_zukunft)):
            zuku_list[i+1] =  ("Zeit: {} ({}) {:3} Dose: {} {:15}".format(
                                        self.list_aktionen_zukunft[i][0],                  \
                                        self.list_aktionen_zukunft[i][3],                  \
                                        ONOFF[self.list_aktionen_zukunft[i][5]] ,          \
                                        self.list_aktionen_zukunft[i][4],                  \
                                        self.list_zimmer [self.list_aktionen_zukunft[i][4]-1] )) 
            zuku_list.append("")   

    #    return (self.list_aktionen_past, self.list_aktionen_zukunft)
        return (past_list, zuku_list)

#----------------------------------------------
    def _ausgabe_liste(self):
# was solen wir ausgeben?  
#
 
        self.actionList.print_actions(self.list_tage, self.list_device, self.list_zimmer)	    # alle gefundenen Aktionen in Listen ausgeben
#
#
#---------------------------------------------------------------
#------ Funktion do_setup
#--------------------------------------------------------------- 
    def _do_setup(self):

        self.myprint (DEBUG_LEVEL1, "\t" + progname + "setup MySequencer")  

        try:
            locale.setlocale(locale.LC_TIME , 'de_CH')
        except:
            self.myprint (DEBUG_LEVEL0, "\t" + progname + "setzen Locale geht nicht, prüfe mit Befehl locale -a ")
        
        
        self.myconfig = ConfigRead(debug_level = self.debug)     # Create Instance of the ConfigRead Class

        self.myprint (DEBUG_LEVEL3, "\nseq:Configdictionary before reading:")
        if (self.debug > 2):
            for x in cfglist_seq:
                print ("{} : {}".format (x, cfglist_seq[x]))

    # we use the configfile given by switcher, could also use our own
    # all keys found in cfglist_seq are read from the config file   <-------------
        ret = self.myconfig.config_read (self.configfile ,config_section, cfglist_seq)  # call method config_read()
        self.myprint (DEBUG_LEVEL1,  "config_read() returnvalue: {}".format (ret))	# für log und debug
 
        self.myprint (DEBUG_LEVEL3, "\nseq:Configdictionary after reading:")
        if (self.debug > 2):
            for x in cfglist_seq:
                print ("{} : {}".format (x, cfglist_seq[x]))

        # aus den eingelesenen Werten werden hier nur 2 verwendet:
        #       ist time adjust verlangt
        #       ist Berücksichtigung Sommer/Winterzeit verlangt 
        try:
        # input comes from configfile
            self.do_adjustTime = int(cfglist_seq ["adjust_needed"])    
            self.do_adjustDaylight_saving = int(cfglist_seq ["daylight_saving"])
        except KeyError :
            self.myprint (DEBUG_LEVEL0, progname + "KeyError in cfglist_seq, check values!")   

       
        
        # print to log was verlangt ist
        if self.do_adjustTime > 0:
            self.myprint (DEBUG_LEVEL1, "\t" + progname + "adjust Time verlangt") 
        else:
            self.myprint (DEBUG_LEVEL1, "\t" + progname + "adjust Time NICHT verlangt")     

        if self.do_adjustDaylight_saving > 0:
            self.myprint (DEBUG_LEVEL1, "\t" + progname + "adjust Sommerzeit verlangt") 
        else:
            self.myprint (DEBUG_LEVEL1, "\t" + progname + "adjust Sommerzeit NICHT verlangt") 


    #   create instance of Class ActionList
        self.actionList=ActionList(self.debug, self.path)      # Instanz der actionLister Class
    # 
        self.myprint (DEBUG_LEVEL0 ,progname +  "object created: {}".format(self.actionList))
        
    # # Einlesen und Parsen der Steuer-Files              alles neu juni2018
        ret, self.file_id = self.actionList.get_actionList (self.list_tage, self.list_device, self.list_zimmer, cfglist_seq)
#
#   nun sind alle Aktionen aus den XML-Files eingelesen und versorgt in den Listen list_tage, list_device und zimmer
#
        #print what we got back from actionList Class
        if (self.debug > 2):
            print ("\nsequencer.py: got these lists from class actionList: <------------")
     
            # print all days and actions
            print ("Anzahl Tage gefunden: {}".format(len(self.list_tage)))
            for v , tag in enumerate(self.list_tage):
                print ("Tag: {}".format(v))
                for action in tag:
                    print ("action:{}".format(action))

        # print all devices and all days and all actions
           
          #  print ("\nAnzahl Dosen gefunden: {}".format(self.anz_dosen_xml))
            for i, dose in enumerate (self.list_device):     
                print ("Device: {}".format(i))

                for y, tag in enumerate (self.list_device[i]):
                    print ("Tag: {}".format(y))

                    for action in tag:
                        print ("action:{}".format(action))
            

        # print alle gefundenen Zimmer
        #    print (" ")
        #    print (self.list_zimmer)
        #    print (" ")
        

        self.anz_dosen_xml = self.actionList.show_anzdevices()

        swdosconf = SWDos_conf (debug = self.debug, path = self.path)   # instanz der Klasse erstellen

        self.myprint (DEBUG_LEVEL0 ,"\t" + progname +  "object created: {}".format(swdosconf))
        self.anz_dosen_config = swdosconf.read_dosenconfig()

        self.myprint (DEBUG_LEVEL1, "\t" + progname +  "Setup, Anz. Dosen in swdosen.ini:{}".format( self.anz_dosen_config))
        #Anzahl Dosen feststellen: loop über alle Saisons, alle Tage und schauen, wo maximum ist

        # anzahl Dosen in XML File kann verschieden sein von Anzahl in swdosen.ini 
        self.myprint (DEBUG_LEVEL2, "\t" + progname +  "Setup, Anz. Dosen (XML)/swdosen.ini:{}/{}".format (self.anz_dosen_xml,self.anz_dosen_config ))
        
        # check anzahl dosen
        if self.anz_dosen_xml >= self.anz_dosen_config:
            self.myprint (DEBUG_LEVEL0, "\t" + progname +  "Nehme Anzahl Dosen aus swconfig.ini, Anzahl:{}".format(self.anz_dosen_config ))
        else:
            self.myprint (DEBUG_LEVEL0, "\t" + progname +  "Achtung: in XML File sind weniger Dosen definiert als in swdosen.ini !")
            self.myprint (DEBUG_LEVEL0, "\t" + progname +  "Nehme Anzahl Dosen aus xml File, Anzahl:{}".format(self.anz_dosen_xml))
            self.anz_dosen_config = self.anz_dosen_xml


     #   print ("Ausgabe")
        for y in range (len(self.list_device)):
            for i in range (len(self.list_device[0])):
                anz= (len(self.list_device[0][i]))
                if (anz >  self.anz_devices): self.anz_devices=anz
        self.anz_devices -= 1      # liste hat 5 elemente , es gibt aber -1 dosen
        self.myprint (DEBUG_LEVEL2, "\t" + progname + "es wurden maximal {} Devices gefunden".format( self.anz_devices))
#        
        for s in self.list_zimmer:                           # longest zimmer string feststellen
            if len(s) > self.maxchar_zimmer:
                self.maxchar_zimmer = len(s)


        #      self.callback (UPDATE_EVENT, ....)    # notify Update zimmer
        self.callback.handle_sequencer_event ( [   UPDATE_EVENT, 
                                            self.list_zimmer, 
                                            NOTUSED, 
                                            NOTUSED, 
                                            NOTUSED,
                                            NOTUSED,
                                            "00.00",
                        ] )                      #   <<<<----Time of day event    midnight reached    uni2018     
                
     #   self._ausgabe_liste()  # lokale Funktion, keine Parameter 
     

        if ret > 0 :
            sys.exit(2)             ## xxx  anpassen !!
#----------------------------------------------------------------------
#