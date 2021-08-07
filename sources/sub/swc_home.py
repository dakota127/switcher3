#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class SWHome 
#   
#   Diese Class kapselt die Dosen in einem Haus
#
#   diese Class erbt von der MyPrint Class
#   diese Class benutzt die Class ConfigRead
#   
#   Feb 2021 
#************************************************
#
import os
import sys
import time
from time import sleep
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.myconfig import ConfigRead
from sub.swc_dosconf import SWDos_conf          # classe anzahl Dosen in swdosen.ini File
from sub.swc_dose import Dose                   # Class Dose, fuer das Dosenmanagement
import RPi.GPIO as GPIO         #  Raspberry GPIO Pins
import json


DEBUG_LEVEL0=0                      
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
home_button  = 13
home_led = 6

# objekte (Instanzen von Klassen)
myconfig = None
swdosconf = None

# messages to frontend
TOFE_DONEDEV    = 1
TOFE_DONESWITCH = 2
TOFE_INITDEV    = 3

# message from Frontend
FROMFE_DEVTOG   = 1
FROMFE_DEVTAUTO = 2
FROMFE_SWITOG   = 3
FROMFE_ALLAUTO  = 4
FROMFE_ALLOFF   = 5
FROMFE_ALLON    = 6
FROMFE_STAT     = 7
FROMFE_SHOW_LIST    = 15
FROMFE_SHOW_STATUS  = 16
FROMFE_SHOW_LOG     = 17
FROMFE_SHOW_WETTER  = 18


# parameter for callback from sequencer class
# values Parmameter1
ACTION_EVENT                = 1
ACTION_EVENT_FRAME1         = 1
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

HOMESTATE={0:'Niemand daheim', 1:'Jemand zuhause'} 
MANRESET={0:'Nie', 1:'Um Mitternacht'} 

progname = "swc_home "
configfile_name = "swconfig.ini"
config_section = "home"                # look up values in this section

#  Values (Directory) für swHome Class --------------
cfglist_home = {
        "gpio_home_led"     : 6,
        "gpio_home_button"  : 13,
        "manuell_reset"     : 1,
    
        }



#----------------------------------------------------
# Class Definition MyHome, erbt vom MyPrint
#----------------------------------------------------
class SwHome (MyPrint):
    ' klasse SwHome '


    def __init__(self, debug, path, conf, test, mqtt_client, connector):  # Init Funktion
        self.errorcode = 8
        self.debug=debug
        self.path = path
        self.configfile = conf          # pfad  main switcher
        self.mqttc = mqtt_client
        self.connector = connector
        self.dosenlist=[]                        # list von Doseninstanzen
        self.anz_dosen_config = 5
        self.payload2 = ""
        self.payl = ""
        self.daheim = 0
        self.zuhause = 0
        self.mqtt_connect = 1
        self.ret = 0
        self.dos = None
        self.data = ""
        self.testmode = test             # passed from switcher3 aus Config File: Testmode Ja/Nein
        self.home_led = 6               # default value
        self.home_button = 13           # default value
        self.manuelle_reset = 0         # reset manuell geschaltete dosen (aus swconfig.ini)
    #    self.anz_dosen_confighome_list = []
        self.are_actions_before_actual_time = True
        self.myprint (DEBUG_LEVEL1, "\t" + progname + "_init called")
        
#      config=ConfigRead(self.debug)        # instanz der ConfigRead Class
#       create Instance of SwConnector Class  
  #      self.swconnector = SwConnector ( debug = self.debug, 
 #                                       endpoint = 1,
   #                                     mqtt_client = self.mqttc,
    #                                    callback = self.from_frontend)
        self._do_setup()
       
        self.errorcode=0    # init SwHome ok

#-------------------------------------------
    # __repr__ function SwHome
    # 
    def __repr__ (self):

        rep = "SwHome (" + str(self.testmode )  + ")"
        return (rep)


#---------------------------------------------------------------
#------ Funktion do_setup
#--------------------------------------------------------------- 
    def _do_setup(self):
        global myconfig

        self.myprint (DEBUG_LEVEL2, "\t" + progname + "setup SwHome")  

        myconfig = ConfigRead(debug_level = self.debug)     # Create Instance of the ConfigRead Class

        self.myprint (DEBUG_LEVEL3, "\nswhome: Configdictionary before reading:")
        if (self.debug > 2):
            for x in cfglist_home:
                print ("{} : {}".format (x, cfglist_home[x]))

    # we use the configfile given by switcher, could also use our own
        ret = myconfig.config_read (self.configfile ,config_section, cfglist_home)  # call method config_read()
        self.myprint (DEBUG_LEVEL1,  "config_read() returnvalue:{}".format (ret))	# für log und debug
 
        self.myprint (DEBUG_LEVEL3, "\nswhome:Configdictionary after reading:")
        if (self.debug > 2):
            for x in cfglist_home:
                print ("{} : {}".format (x, cfglist_home[x]))
         
        if ret > 0 :
            sys.exit(2)             ## xxx  anpassen !!


        try:
        # input comes from configfile
            self.home_led =         int(cfglist_home["gpio_home_led"])
            self.home_button =      int(cfglist_home["gpio_home_button"])
            self.manuelle_reset =   int(cfglist_home["manuell_reset"])
        except KeyError :
            self.myprint (DEBUG_LEVEL0, progname + "KeyError in cfglist_home, check values!")   

        

        GPIO.setup(self.home_button, GPIO.IN)
        GPIO.setup(self.home_led, GPIO.OUT)
        GPIO.output(self.home_led, False)        # set led off bei beginn
        GPIO.add_event_detect(self.home_button, GPIO.FALLING, callback = self.switch_change_local,
                              bouncetime = 300) # 20ms debounce time
       
        swdosconf = SWDos_conf (debug = self.debug, path = self.path)   # instanz der Klasse erstellen

        self.myprint (DEBUG_LEVEL0 ,progname +  "object created:{}".format(swdosconf))
        self.anz_dosen_config = swdosconf.read_dosenconfig()
        self.myprint (DEBUG_LEVEL1, "\t" + progname +  "Anzahl Dosen in swdosen.ini:{}".format( self.anz_dosen_config))

        # instances of dosen class instantiieren
        for i in range(self.anz_dosen_config):
            self.dos = Dose(i, self.testmode, self.debug, self.configfile, self.mqtt_connect, self.mqttc, self.handle_device_event)
            if self.dos.errorcode == 99:
                self.myprint (DEBUG_LEVEL1, "\t" + progname +  "Dose{} meldet Fehler:{}".format (i+1, self.dos.errocode))	 
                raise RuntimeError("\t" + progname + 'ernsthafter Fehler, check switcher2.log <----')
            else:
                self.dosenlist.append(self.dos)           # es wird dose 1 bis anz_dosen 
        
        for dose in self.dosenlist:
            self.myprint (DEBUG_LEVEL0 ,progname +  "object created:{}".format(dose))
    

        self.test_dosen()
        self.myprint (DEBUG_LEVEL1, "\t" + progname + "setup SwHome DONE ")  
        return

#---------------------------------------------------------------        
# handles terminate request from switcher3 
#---------------------------------------------------------------
    def all_off(self):
        self.myprint (DEBUG_LEVEL1, "\t" + progname + "all_off called")  

        
    # alle dosen ausschalten
        for dose in self.dosenlist:
                dose.schalten_manuell(0)
        
        self.connector.terminate()              # do terminate in the connector


        return

#---------------------------------------------------------------      
# gibt status des Homes zurück
# is a list of three lists
#---------------------------------------------------------------
    def home_status (self):

        self.myprint (DEBUG_LEVEL2,  "\t" + progname + "home_status() called")
        ho = 0
        home_list = []              # create an empty list
        anzahl_on = 0               # anzahl schaltaktionen on
        anzahl_off = 0              # anzahl schaltaktionen off
        home_list.append ([])       # first list home stati     (also jemand daheim oder nicht, als int und text)
        home_list.append ([])       # second list dosen stati   (alle dosen und deren status)
        home_list.append ([])       # third list total anz schaltaktionen  (2 items, on und off)
        
        # fill first list
        if self.zuhause:            # assemble items of first list
            ho = 1
        home_list[0].append (ho)                 # int
        home_list[0].append (HOMESTATE[ho])      # text
        home_list[0].append (MANRESET[self.manuelle_reset])     # manuell geschaltete wann resetten ?
        home_list[0].append (self.anz_dosen_config)                 # manzahl dosen definiert
        
        # fill second list  
        for dose in self.dosenlist:          
            dosstat = dose.show_status()
            home_list[1].append (dosstat)

            anzahl_on = anzahl_on + dosstat[10]
            anzahl_off = anzahl_off + dosstat[11]
        
        # fill third list
        home_list[2].append(anzahl_on)  
        home_list[2].append(anzahl_off)  

        # three lists done

        self.myprint (DEBUG_LEVEL2,  "\t" + progname + "home_list:{}".format(home_list))

        return (home_list)




#---------------------------------------------------------------        
# handle callbacks from dosen  (called whenever a device switches)
#---------------------------------------------------------------
    def handle_device_event (self,dose_list):
        self.myprint (DEBUG_LEVEL2,  "\t" + progname + "handle_device_event called, dose_list:{}".format( dose_list)) 
        self.payload = ["done_dev"  , dose_list]   # publish ack on topic  
        self.payl=json.dumps(self.payload)          # umwandeln in JSON Object (also ein String)   

        self.ret = self.connector.transmit (self.payl)      # <------------------  transmit to frontend --------
        if (self.ret > 0):
            self.myprint (DEBUG_LEVEL0,  "\t" + progname + "transmit returns:{} ".format(self.ret))


#---------------------------------------------------------------        
# handle messages from frontend via switcher3 switchboard
#   these messages have their point of origin in the javascript code in index.html
#   they are sent from the browser to the swserver which sends appropriate asnyc messages
#   via mqtt to the switcher3, which routes them to the swhome class
#   
#   All these messages have to do with switching of devices and changing of states eg. for zuhause/not zuhause
#   Messages that ev. will switch devices are routed to the correct Dose
#   The message 'initial' also comes from the Browser upon completing loading the page. On this message we will send
#   a list of all dosenstati - so the browser can update all fileds and button on the page
#   
#---------------------------------------------------------------
    def messageIn (self, message):              # message from Frontend via switcher3

        self.myprint (DEBUG_LEVEL2,  "\t" + progname + "messageIn called, msg:{}". format(message))  


        if (message[0] == "tog_dev"):  
            dos = message[1]
            print (dos)
            if dos <= self.anz_dosen_config:            # check device nummer, must in range
                self.dosenlist[dos-1].umschalten()      # schalte dose um
            else :
                self.myprint (DEBUG_LEVEL0,  "\t" + progname + "tog_dev, device ungültig:{}". format(dos)  )
      
        elif (message[0] == "tog_home"):  
            self.do_zuhause()                       # wechsel von jemand daheim zu niemand daheim oder vice versa
       
        elif (message[0] == "auto"):                # diese dose auf modus auto setzen (und ev. schalten)
            self.dosenlist[message[1]-1].set_mod_auto()  
    
        elif (message[0] == "all_auto"):
            for dose in self.dosenlist:
                dose.set_mod_auto()                 # alle dosen set modus auf auto (und ev. schalten)
    
            
        elif (message[0] == "all_on"):
            for dose in self.dosenlist:
                dose.schalten_manuell(1)                 # alle dosen einschalten und modus auf manuell setzen
     

        elif (message[0] == "all_off"):
            for dose in self.dosenlist:
                dose.schalten_manuell(0)                 # alle dosen ausschalten und modus auf manuell setzen
     
     #       
        else:

            self.myprint (DEBUG_LEVEL0, "\t" + progname + "invalid message received:{}". format(message))

#---------------------------------------------------------------        
# function handle event from sequencer
#  the sequencer can send three types of events:
#  1. TIME_OFDAY_EVENT  : like midnight, noon
#  2. UPDATE_EVENT      : to update data in dosen
#  3. ACTION_EVENT      : a device has switched its state from ON to OFF or from OFF to ON
#---------------------------------------------------------------
    def handle_sequencer_event (self, command):
        self.myprint (DEBUG_LEVEL2, "\t" + progname + "handle_sequencer_event called:{}/{}/{}/{}/{}/{}/{}". format(command[0],command[1],  \
                                                                                               command[2],command[3],command[4],command[5],command[6]   ))


        if (command[0] ==TIME_OFDAY_EVENT):
            self.myprint (DEBUG_LEVEL2, "\t" + progname + "ist time of day event")
            if (command[1] == ACTUAL_NOW):
                self.myprint (DEBUG_LEVEL2, "\t" + progname + "time is now actual time")
                self.are_actions_before_actual_time = False
                for dose in self.dosenlist:
                    dose.set_wiestatus()                    # schalte dose gemäss dem internen status (falls modus auto ist)

            elif (command[1] == MIDNIGHT):
                self.myprint (DEBUG_LEVEL2, "\t" + progname + "a new day has begun")
                if self.manuelle_reset == 1:
                    self.myprint (DEBUG_LEVEL2, "\t" + progname + "set manuelle OFF")
                    for dose in self.dosenlist:
                        dose.set_mod_auto()                  # set modus der Dose auf auto

        elif command[0] == UPDATE_EVENT:   # command[1] ist list of room-id's
          #  print (command[1])
          # set zimmer in dosen
            for dosennummer, dose in enumerate(self.dosenlist): 
                dose.set_zimmer(command[1][dosennummer])           # setze den Zimmer namen in die dose


        elif command[0] == ACTION_EVENT:
            self.myprint (DEBUG_LEVEL2, "\t" + progname + "ist action event, dose:{} wie:{}".format(command[2],command[3])) 

            if (self.are_actions_before_actual_time == True):
                self.dosenlist[command[2]-1].schalten_auto_virtuell(command[3])  
            else:  
                self.dosenlist[command[2]-1].schalten_auto(command[3])    
        else:
            self.myprint (DEBUG_LEVEL0, "\t" + progname + "wrong event type:{}".format(command[0])) 


#---------------------------------------------------------------
#------ Funktion do_zuhause ----- wird im callback interrupt aufgerufen
#--------------------------------------------------------------- 
    def do_zuhause(self):
    
        self.daheim = 0

        self.myprint (DEBUG_LEVEL1,  "\t" + progname + "do_zuhause called")  

        if not self.zuhause:     #  was ist der aktive status ?
            self.zuhause = True 
            self.daheim = 1 
            if self.home_led > 0:      # if led defined
                GPIO.output(self.home_led , self.zuhause)        # set led on if at home
                                         # hilfsfeld   
            self.myprint (DEBUG_LEVEL1, "\t" + progname + "Jemand daheim, nicht manuelle Dosen aus")   
            for dose in self.dosenlist:
                dose.set_zuhause()                      # schalte ev. dose aus, weil nun jemand daheim ist
        else:
            self.zuhause = False      #  niemand daheim
            self.daheim = 0          # hilfsfeld
            if home_led > 0:    # if led defined
                GPIO.output(home_led, self.zuhause)        # set led off if NOT at home
        
            self.myprint (DEBUG_LEVEL1, "\t" + progname + "Niemand daheim, setzt Dosen gemaess Dosenstatus")            
            for dose in self.dosenlist:
                dose.set_nichtzuhause()                 # schalte ev. dose ein, weil nun niemand daheim ist

        self.myprint (DEBUG_LEVEL1, "\t" + progname + "home_state now: {}/{}".format (self.daheim,HOMESTATE[self.daheim]))
        # notify frontend

        # send notification to swserver        
        self.payload2 = ["done_home"  , [self.daheim, HOMESTATE[self.daheim]] ]  #   
        self.payl=json.dumps(self.payload2)          # umwandeln in JSON Object (also ein String)    
        self.ret = self.connector.transmit (self.payl)            # <------------------  transmit to frontend --------
        if (self.ret > 0):
            self.myprint (DEBUG_LEVEL0, "\t" + progname +  "transmit returns: {} ".format(self.ret))   
      
        return()	



#---------------------------------------------------------------   
 #  callback eventhandler GPIO.add_event_detect   home / not home
#--------------------------------------------------------------- 
    def switch_change_local(self,pin):
        time.sleep(0.05)                            # simple debounce
        if GPIO.input(pin) == 0:
            self.do_zuhause()                       # do everything needed for changing state 
        else:
            pass    

#---------------------------------------------------------------      
# Funktion Dosen kurz einschalten (nur bei testmode="Ja" im configfile)
#---------------------------------------------------------------
    def test_dosen(self):

#  mache dies nicht bei Testmode  Nein und auch nur bei schaltart =1 (testbett)
        if  not self.testmode:
            return
     
        self.myprint (DEBUG_LEVEL1,  "\t" + progname + "testmode=Ja in Configfile=1, also mache Test_dosen")
        time.sleep(1)
        for dose in self.dosenlist:          
            dose.schalten_auto(1)                    # schalte dose ein
            time.sleep(0.5)
            dose.schalten_auto(0)                    # schalte dose aus
        self.myprint (DEBUG_LEVEL1,  "\t" + progname + "Test_dosen done")
        time.sleep(1)    

#-------------Terminate Action PArt ---------------------------------------
# cleanup GPIO PIns
#------------------------------------------------------------------------
    def __del__(self):
        self.myprint (DEBUG_LEVEL3, "\t" + progname + "del called")
        



   
# ************************************************** 		


#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("MyHome.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
