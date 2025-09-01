#!/usr/bin/python3
# coding: utf-8
#
# ***********************************************************
#
# This is program ONE of a suite of two programs for the Switcher3 System
#  
# This Programm is the MAIN programm 
# it uses several objects (instances of classes) to do its thing 
#
# Object swHome contains everything in a home (Dosen, Stati)
# Object Sequencer creates events based on the switching actions defined in the XML Control file
# Object SwConnector ist used to communicate with the swserver Programm
# Object Wetter collects wetter data (used only if configured in swconfig.ini)
#
# Runs under Python3   and NOT tested under Python2 
# This programm creates two threads:
#       the sequencer runs as a thread
#       the blink thread simply binks an LED
#       and: function notifySwitcher() is a mqtt callback and runs as a thread
# 
# Peter Boxler (March 2020)
# *********************************************************

import paho.mqtt.client as mqtt
import argparse, os, sys
import time
from datetime import date, datetime, timedelta
import threading
from sub.myprint import MyPrint             # Class MyPrint replace print, debug output
from sub.mymqtt import MQTT_Conn              # Class MQTT_Conn handles MQTT stuff
from sub.swc_sequencer import MySequencer              # Class Sequencer
from sub.swc_home import SwHome                   # Class MyHome
from sub.myconfig import ConfigRead
from sub.swc_connector import SwConnector           # Class SwConnector
import RPi.GPIO as GPIO                         #  Raspberry GPIO Pins
from sub.swc_wetter import Wetter 
import json
from sub.swdefstatus import info_gross
from sub.swdefstatus import info_klein
import socket
import signal

#----------------------------------------------------------
# ---------------------------------------------------------
# Change Version of switcher3 here 
# 
switcher_version = "3.7 (Aug.2025)"
#---------------------------------------------------------
#--------------------------------------------------------

# Define Variables

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
debug=0
terminate = False

# MQTT Topics
MQTT_TOPIC_SERVPUB      =     "swi/as"           # PUB sending to flask server
MQTT_TOPIC_SERVPUB_AS   =     "swi/snyc"           # PUB sending to flask server
MQTT_TOPIC_SWIPUB       =     "serv/as"           # PUB sending to flask server
MQTT_TOPIC_RESP         =       "response"           # PUB sending to flask server

MQTT_TOPIC_PUB =   "test2"
MQTT_TOPIC_SUB =   "test"
MQTT_TOPIC_PUBSERV =   "toserver"           # PUB sending to flask server
MQTT_TOPIC_SUBSWIT =   "toswitcher"         # SUB receiving at switcher from flask server
mqtt_broker_ip_cmdline = ""     # ipc adr from commandline
mqtt_connect = False
mqtt_error = 0

# instances of classes
myprint = None
mymqtt  = None
swhome  = None
swconnector = None
swinterface= None
my_wetter = None
#myqueue = None

wait_time = 10
retry = False                   # do not retry on connect to brokaer
sequencer = None
zuhause = False            # nobody home
dosen=[]                        # list von Doseninstanzen
anz_dosen_config = 5
progname = "switcher3 "
logfile_name = "switcher3.log"
configfile_name = "swconfig.ini"
config_section = "switcher"                # look up values in this section

gpio_blink = 5              # default value
testmode = "Nein"              # aus Config File: Testmode Ja/Nein
testmodebol = False
fortschritt = 0
TRUEFALSE=[False,True]
JANEIN=["Nein","Ja"]
MSGART= ["ASYNC", "SYNC" ]
mqtt_broker_ip_cmdline = ""     # ipc adr from commandline
blink_thread=0                  # thread handle
term_verlangt = 0             # generelle term Variable, 1 heisst fuer alle Loops: beenden
reboot_verlangt = 0           # reboot Pi am Ende des Herunterfahrens von switcher

days_str = ""
status_laueft_seit = 0          # Anzahl Tage die der Switchr gelaufen ist seit letztem Start
start_switcher = 0
setup_fortschritt = 0
time_old = 0
adjust_minutes = 0
year_week = 0
wetter = "Nein"
host_name = " " 
host_ip = " "
general_error = 0

# ***** Variables *****************************
#   Struktur (Directory) der Daten, die aus dem Configfile swconfig.ini gelesen werden
# s  hier die defaultwerte der 'variablen'
cfglist_swi = {
        "testmode"          : "Nein",          # testmode Ja/Nein
        "wetter"            : "Nein",          # wetter benötigt JA/Nein
        "gpio_blink"        : 5,               # gpio pin blink led
        "reserve"           : 'reservedefault',   #
        "debug"             : 0,               #  debug flag, wie commandline parm -d = 1,-D = 2, -A = 3         
        }


ALIVE_INTERVALL_0 = 60          # sec between alive log entry (TESTMODE)
ALIVE_INTERVALL_1 = 9000        # sec between alive log entry (normal), also: 9000/60  gleich 90 min min 
ALIVE_INTERVALL_2 = 86400       # in Sekunden, also: 86400 /60  gleich 1440 min gleich 24 Std    


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

MSG_ASYNC = 0
MSG_SYNC  = 1

# General error Codes
MQTT_ERROR = 55


# define Python user-defined exceptions
class Error(Exception):
    """Base class for other exceptions"""
    pass


class ThreadError(Error):
    """Raised when the input value is too small"""
    pass



# ***** Variables *****************************

# ***** Class blink-led **************************
#-------------------------------------------------
class myBlink(threading.Thread, MyPrint):
  
    def __init__ (self, gpio_blink):
        super().__init__()
        self.myprint (0, "myBlink _init called")
        self.pin = gpio_blink

    def run(self):
        while True:
            for i in range(2):
                GPIO.output(self.pin, True)
                time.sleep(0.1)
                GPIO.output(self.pin, False)
                time.sleep(0.1)
            for i in range(4):
                time.sleep(1)     

#-- Function to handle kill Signal (SIGTERM)---------------------
#----------------------------------------------------------
def sigterm_handler(_signo, _stack_frame):
    global term_verlangt
    # Raises SystemExit(0):
    myprint.myprint (DEBUG_LEVEL0,  "SIGTERM/SIGHUP Signal received in switcher3")   # fuer Tests
    term_verlangt=1
    swi_terminate(9)                    #      alles gracefully beenden, dann fertig
    raise SystemExit(2)


# ***** Function Parse commandline arguments ***********************
#----------------------------------------------------------
# get and parse commandline args
def argu():
    global debug, mqtt_broker_ip_cmdline, retry

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", help="small debug", action='store_true')
    parser.add_argument("-D", help="medium debug", action='store_true')
    parser.add_argument("-A", help="details debug", action='store_true')
    parser.add_argument("-r", help="retry indicator", action='store_true')
    parser.add_argument("-i", help="IP Addr", type=str)
    args = parser.parse_args()

    if args.d:
        debug=DEBUG_LEVEL1
    if args.D:
        debug=DEBUG_LEVEL2
    if args.A:
        debug=DEBUG_LEVEL3
    if args.r:
        retry = True
    if args.i: 
       mqtt_broker_ip_cmdline = args.i
 
    return(args)
#----------------------------------------------------------


#-- Function to handle kill Signal (SIGTERM)---------------------
#----------------------------------------------------------
def sigterm_handler(_signo, _stack_frame):
    global term_verlangt
    # Raises SystemExit(0):
    myprint.myprint (DEBUG_LEVEL0,  progname + "SIGTERM/SIGHUP Signal received")   # fuer Tests
    term_verlangt = 1
    swi_terminate(9)                    #      alles gracefully beenden, dann fertig
    raise SystemExit(2)



#*********  endebehandlung **********
#----------------------------------------------------------
def swi_terminate(was):
    global GPIO, mymqtt_client, my_wetter
#
    myprint.myprint (DEBUG_LEVEL0,   progname + "terminate() called, was: {}".format(was))			

    
    swhome.all_off()                  # do terminate in swhome
        
    myprint.myprint (DEBUG_LEVEL0,   progname + "terminating")
    
    sys.exit(2)                         #  fertig lustig

  # terminating switching    Mai 2021

#---------------------------------------------------------------       
# --- do subscribe and publish
# --- needs to be called after initial connection and after reconnect
#-------------------------------------------------------------       
def do_sub():
    return

#-------------------------------------------
# Python program to copy or clone a list
# Using the Slice Operator
def Cloning(li1):
    li_copy = li1[:]
    return li_copy


#*********  check mqtt connection **********
#----------------------------------------------------------
def check_mqtt():
    
#  ---------------------------
#   im Oktober 2022 dies eingefügt, weil ev. Ipadr bei reboot des Pi nicht geholt werden kann, da beim start network unavailable ist
#   wir versuchens das nochmals
    global host_name, host_ip
    if host_ip == "??":
        host_name, host_ip = get_Host_name_IP()
# -----------------------------------------------

    myprint.myprint (DEBUG_LEVEL1,   progname + "check_mqtt() called")			
    connect, error = mymqtt.get_status()
    if not connect:
        myprint.myprint (DEBUG_LEVEL0,   progname + "no connection, connect:{}, err:{}".format(connect,error))	

        mymqtt.reconnect()




#---------------------------------------------------------------       
# --- get all the info (grosser Status für Info Seite)
# --- 
#-------------------------------------------------------------       
def assemble_info():

    seq_list = sequencer.show_status()                  # get info from Sequencer Class
    home_list = swhome.home_status()                    # get info from swHome Class 
    # print (seq_list)                                    # this is a list of three lists
    
    adj_sunset_time = seq_list [0]                  # ist J oder N
    adj_sommerwinter = seq_list [14]                # ist J oder N
    sommerwinter_zeit = adj_winter = seq_list [15]  # ist W oder S oder -
   

    info_gross[0][1] =  switcher_version + " / " + str(seq_list[10])       # item 1: switcher version/anzahl Dosen
    info_gross[1][1] =  seq_list[11]                                       # item 2: start date/time
    info_gross[2][1] = days_str                                            # item 3: Laufzeit Tage
    info_gross[3][1] = "{:05d} / {:05d}".format (home_list[2][0],home_list[2][1])   # anzahl schaltaktionen
    #if seq_list [0] > 0:                   # adjust times verlangt
    #    info_gross[4][1] = "{0:0>2}".format(str(seq_list[1]))  + " / " + "{0:0>3}".format(str(seq_list[2]) + " / " + "{}".format(seq_list[14]))
    #else:
    #    info_gross[4][1] = "{0:0>2}".format(str(seq_list[1]))  + " / n.a / " + "{}".format(seq_list[14])
    
    #    info_gross[4][1] = "nicht konfiguriert"

    # zeile 4: Info über  schaltzeiten ajustieren
    # [4][1]: woche / 00 / Ja / W
    info_gross[4][1] = "{0:0>2}".format(str(seq_list[1]))  + " / " + "{:s}".format(str(seq_list[2])) + " / " + adj_sunset_time + " / " + adj_sommerwinter  \
        + " / "  + sommerwinter_zeit + " / " + "{}".format(seq_list[16][0]) + " / " + "{}".format(seq_list[16][1]) + " / " + "{}".format(seq_list[16][2])

    info_gross[4][1] =  adj_sunset_time + " / " + adj_sommerwinter + " / " + "{0:0>2}".format(str(seq_list[1]))  + " / " + "{:s}".format(str(seq_list[2]))    \
        + " / "  + sommerwinter_zeit + " / " + "{}".format(seq_list[16][0]) + " / " + "{}".format(seq_list[16][1]) + " / " + "{}".format(seq_list[16][2])
  #  info_gross[4][1] = "{0:0>2}".format(str(seq_list[1]))  + " / " + adj_time + " / " + adj_summer
    # print (info_gross[2][1])
    info_gross[5][1] = swhome.home_status()[0][1]       # zuhause status
    info_gross[6][1] = seq_list[3]                      # file ID des XML Files
    info_gross[7][1] = testmode + " / " + str(debug)    # testmode und debug
    info_gross[8][1] = seq_list[12]                     # aktueller tag und Zeit
    info_gross[9][1] = seq_list[4]                      # Aktueller Wochentag
    info_gross[10][1] = seq_list[5]                     # Anzahl Aktionen am heutigen Tag
    info_gross[11][1] = seq_list[6]                     # davon ausgeführt
    info_gross[12][1] = seq_list[7]                     # wartend bis
    info_gross[13][1] = seq_list[8]                     # nächste aktion
    info_gross[14][1] = seq_list[9]                     # letzte aktion
    info_gross[15][1] = wetter                          # wetter konfiguierte ja/nein
    info_gross[16][1] = swhome.home_status()[0][2]      # reset manuell geschaltete dosen, wann
    info_gross[17][1] = host_name + " / " + host_ip     # host name und IP
    return (info_gross)

#---------------------------------------------------------------       
# --- get all the info (kleiner Status für Home Seite)
# --- 
#-------------------------------------------------------------       
def assemble_info_2():

    seq_list = sequencer.show_status()
   
    info_klein[0][1] = time.strftime("%d.%B %Y : %H.%M")        # datum und Zeit 
    info_klein[1][1] = seq_list[4]                             # wochentag
    info_klein[2][1] = seq_list[8]         
    info_klein[3][1] = seq_list[9]

    if wetter == "Ja":
        we_list =  my_wetter.get_wetter_data_part()
        info_klein[4][1] = we_list[0]
        info_klein[5][1] = we_list[1]
        # clone this list
        li2 = Cloning(info_klein)
    
    else:
        info_klein[4][1] = "not def"
        info_klein[5][1] = "not def"
        # clone this list and remove the last two items if wetter is not defined
        li2 = Cloning(info_klein)
        li2.pop()           # remove Wetter innen
        li2.pop()           # remove Wetter aussen
    
    return (li2)


#-------------------------------------------------
# get hostname und IP
#----------------------------------------------
def get_Host_name_IP():

# Note: bei frischen reboot des Pi kann hier die Ipadr nicht geholt werden, da network nochunavailable ist <----------
#   darum versuchen wir es später wieder in Funktion check_mqtt()
#   ist hack, aber ok
    host = " "
    local_ip_address = " "
    host = socket.gethostname()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(10)
    try:
            # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        local_ip_address = s.getsockname()[0]
    except:
        local_ip_address = '??'
        myprint.myprint (DEBUG_LEVEL0,   progname + " Fehler beim Bestimmen der ipadr, set to ?? and continue..")

    finally:
        myprint.myprint (DEBUG_LEVEL0,   progname + " ----> IPAdr this machine:{}".format(local_ip_address))
    
    return (host, local_ip_address)


# --- handle messages from frontend
# this is a callback handler and therefor runs in a seperate thread
# we need to do a try/except to catch errors in the thread
#-------------------------------------------------------------       
def notifySwitcher (art , message):
    
    myprint.myprint (DEBUG_LEVEL1,   progname + "notifySwitcher called, art:{}, msg:{}".format(MSGART[art], message))	
    #if isinstance(message, str) == True:
       # print ("message is string")

    # do this and call the function that does the stuff
    try:
        do_notifySwitcher (art , message)
    except Exception:
        myprint.myprint_exc  ("switcher3: notifySwitcher() etwas Schlimmes ist passiert.... !")
    finally:
        pass
    #  print ("notifySwitcher finally reached") 
    # terminate Thread by returning 
    # will be restarted with the next request 
        return




#---------------------------------------------------------------       
# --- handle messages from frontend
# this is a callback handler and therefor runs in a seperate thread
#
# ---   called from Connector Class - the requests originate in the MAIN program swserver.py
# ---   handles SYNC and ASYNC request  <-----------------
#            different sync commands can come in:
#           'aliste'    server requests action lists of this day
#           'home'      server requests to render the home page and needs all data for the page
#           'wetter'    server requests wetter data
#           'info'      server requests switcher Info
#           'other..'   this commands are routed to the class swhome (mostle manual switching on the GUI)
#--------------------------------------------------------
def do_notifySwitcher (art , message):
    global debug, days_str
#-------------------------------------------------
    # handle SYNC requests  -------------------------
    # they require an answer message with the topic supplied in the incoming message !
    # requests can be aliste, home, info, wetter 
    #---------------------------------------------------------------------------------
    if art == MSG_SYNC:             # sync message received
    
    #   handle sync messages ------------------
    #   pos 0 to 3  :   message number
    #   pos 4 to 19 :   response topic
    #   pos 19 to 25:   request
        msg_numbr = message[:4]
        response_topic = message[4:19]
        response_topic = response_topic.rstrip()
    

        request = message[19:29]

       # print (" REQUEST:{}--".format(len(request)))


        myprint.myprint (DEBUG_LEVEL1,   progname + "msgnumber:{}".format(msg_numbr))
        myprint.myprint (DEBUG_LEVEL1,   progname + "response topic:{}".format(response_topic))

        #prepare some variables that will be sent
      #  days_str    = "{:0>4}".format(status_laueft_seit)      # with leading zeros
        days_str    = str(status_laueft_seit)                   # NO leading zeros

    # check the request that came in
    # currently implemented are     aliste  -> request for lists of past and future actions
    #                               home    -> request for initial data about all devices and such (to build indext.html page)
    #                               info
    #                               wetter
    #

    # -----------aliste ----------------------- aliste --------------------------------------
        if (request.find("aliste") == 0):       # request for list of actions
            myprint.myprint (DEBUG_LEVEL1,   progname + "request aliste gekommen")
            if (sequencer != None):         # wenn object da ist
                pastl ,futurl = sequencer.show_dayactions()   # call a method of the squencer Class, it will provide two lists
                if debug > 2:
                    print ("past_actions: ")
                    for z in pastl:
                        print (z)
                    print ("zukunft_actions: ")
                    for y in futurl:    
                        print (y)

            send_list =[]      # assemble list
            minfo_list = assemble_info()     #request data from sequencer

        # this statement used to produce an error to test try/except  
        #    a= e                # xxx

            # print (minfo_list)
            # we send response that has this format:
            # We send a list of three lists
            #       First list contains Info for the footer
            #       Secons list contains all past actions (of the day)
            #       Third list contains all future actions  (of the day)

            a_list = []
            a_list.append (minfo_list[4][1])   # info for footer (week /adjust minutes)
            a_list.append (0)                   # reserve
            
            send_list.append (a_list)           # first list
            send_list.append(pastl)             # second list past actions of the day
            send_list.append(futurl)            # third list future actions of the day

            payl = msg_numbr + request + json.dumps(send_list)           # umwandeln in JSON Object (also ein String)   

            myprint.myprint (DEBUG_LEVEL1,   progname + "notifySwitcher doing transmit msg")	
            swconnector.transmit (message = payl, topic = response_topic)   

            return



    # -----------home ----------------------- home --------------------------------------
        if (request.find("home") == 0):
            #  server wnats to load the home page, send the data that is shown on the home page
            myprint.myprint (DEBUG_LEVEL1,   progname + "request home gekommen")	
            dos_list= swhome.home_status()      # alle Daten: home_state plus dosenlist

            # Hole alle Daten für den kleinen Status

         #   stat_list = ["Datum: 12. März 2021 : 20.23", "Nächste: Schlafzimmer 21.12 Ein","Letzte: Wohnzimmer 20.05 Ein",  \
         #       "Niemand Zuhause","Temperatur Innen: 22.8","Temperatur Aussen: 19.4"]
    
            info_list = assemble_info_2()

         #   print (info_list)
            # we send response that has this format:
            send_list =[]
            a_list = []
            a_list.append (switcher_version)        # version switcher
            a_list.append (swhome.home_status()[0][3]   )  # ANzahl Dosen definiert
            a_list.append (0)                       # reserve
            send_list.append (a_list)               # info für footer
            send_list.append (info_list)            # die 6 Felder oben an der Seite
            send_list.append ( dos_list)            # liste aller dorsenstatis

      #      if wetter == "Nein":
      #          send_list[1].pop()
      #          send_list[1].pop()

            payl = msg_numbr + request  + json.dumps(send_list)            # umwandeln in JSON Object (also ein String)    
            swconnector.transmit (message = payl, topic = response_topic)   

            return

    # -----------Info ----------------------- Info --------------------------------------
        if (request.find("info") == 0):
            #  server requestas infos
            myprint.myprint (DEBUG_LEVEL1,   progname + "request info gekommen")

            info_list = assemble_info()
           # print (info_list)

            # we send response that has this format:
            # We send a list of two lists
            #       First list is empty (future use)
            #       Secons list contains all info items to be display on the html info page
    
            send_list =[]
            send_list.append([])                # first list empty
            send_list.append (info_list)        # second list info items
    
            payl = msg_numbr + request  + json.dumps(send_list)            # umwandeln in JSON Object (also ein String)    
            swconnector.transmit (message = payl, topic = response_topic)   
            return


    # -----------wetter ----------------------- wetter --------------------------------------
        if (request.find("wetter") == 0):

            send_list = []          # create empty list to send back
            #  server requests wetter data
            myprint.myprint (DEBUG_LEVEL1,   progname + "request wetter gekommen")

            # we send a list of three lists
            #   first list:     one item saying wheter wetter is configured
            #   second list:    two lists of wetter data: first list indoor, second list outdoor
            #                   these list are empty if wetter not configured

            if wetter == "Nein":
                send_list.append ([0])      # first list hat only one item (0 or 1)
                send_list.append ([[],[]])      # two empty lists 
            else: 
                send_list.append ([1])    
                we_list = my_wetter.get_wetter_data_all()      # wetter data holen 
                send_list.append(we_list)

                myprint.myprint (DEBUG_LEVEL0,   progname + "wetter test:{} {}".format(we_list[0],we_list[1]))                                 # xxx
            # --------- weg xxx-----------------------
    
            payl = msg_numbr + request  + json.dumps(send_list)            # umwandeln in JSON Object (also ein String)    
            swconnector.transmit (message = payl, topic = response_topic)   
            return



    #-------------------------------------------------
    # handle ASYNC requests  -------------------------
    # they are handled by the swHome class
    # only deb_off and deb_on are handled here
    # usually these messages are sent by swserver.py if the user changes something in the WebInterface
    # (switch on/off a dose or change at home status)
    #---------------------------------------------------------------------------------

    elif art == MSG_ASYNC:      
        #   handle async messages ------------------
        # check if message is for switcher himself (and not for swhome object)

        # this dbug thing is ot fully implemented, would need more thought and programming
        # objects that are already created will not know of this new debug value
        # so this is a half baked idea  (May 2021)
        for_me = False

        if message[0].find("deb_off") == 0:
            debug = 0
            myprint.set_debug_level(debug)
            for_me = True
        if message[0].find("deb_on") == 0:
            for_me = True
            myprint.set_debug_level(debug)
            debug = 1

        

        if for_me == False :   
        # all other commands are handeld by the swhome class
        # if instance of swhome class exists call its messageIn function
            if (swhome != None):
                swhome.messageIn (message)          # goes to swhome

    # if msg type not SYNC or ASYNC -----------
    else:
        myprint.myprint (DEBUG_LEVEL1,   progname + "notifySwitcher wrong message type:{}".format(art))	

    pass

    

#---------------------------------------------------------------
# Setup routine setup all stuff needed on the switcher side
# #---------------------------------------------------------------
def setup():
    global mymqtt, myprint, mqtt_connect, swhome, swinterface, sequencer, swconnector,my_wetter
    global start_switcher , setup_fortschritt, gpio_blink, wetter, testmode, host_name, host_ip, debug

    debug_konf = 0      # debug aus swconfig.ini  0() oder 1)

    print(progname + "started: {}".format(time.strftime('%X')))   
    argu()                          # get commandline argumants
    path = os.path.dirname(os.path.realpath(__file__))    # current path

    print ("Name logfile: {} ".format( path + "/" + logfile_name) )
    print ("Name configfile: {} ".format( path + "/" + configfile_name) ) 
    
    signal.signal(signal.SIGTERM, sigterm_handler)  # setup Signal Handler for Term Signal
    signal.signal(signal.SIGHUP, sigterm_handler)  # setup Signal Handler for Term Signal

    
   # print ("------> {}|{}".format(host_name,host_ip))
    start_switcher = date.today()
    
    setup_fortschritt = 0

    #Use BCM GPIO refernece instead of Pin numbers
    GPIO.setmode (GPIO.BCM)
    rev = GPIO.RPI_REVISION
    GPIO.setwarnings(False)             # juni2018 ist neu hier, war in gpio_setup()
    
    # create Instance of MyPrint Class 
    myprint = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  path + "/" + logfile_name ) 

   
    myprint.myprint (DEBUG_LEVEL0,  progname + "started <-------------: {}".format(time.strftime('%X')))   
    myprint.myprint (DEBUG_LEVEL0,  progname + "Name logfile: {} ".format( path + "/" + logfile_name) )
    myprint.myprint (DEBUG_LEVEL0,  progname +  "Name configfile: {} ".format( path + "/" + configfile_name) ) 

    host_name, host_ip = get_Host_name_IP()
    
    # Create Instance of the ConfigRead Class
    myconfig = ConfigRead(debug_level = debug)     

    myprint.myprint (DEBUG_LEVEL3, progname + "\nswi Configdictionary before reading:")
    if (debug > 2):
        for x in cfglist_swi:
            print ("{} : {}".format (x, cfglist_swi[x]))

    # Read from Configfile  
    ret = myconfig.config_read (path+"/" + configfile_name ,config_section, cfglist_swi)  # call method config_read()
    myprint.myprint (DEBUG_LEVEL1, progname +  "swi:config_read() returnvalue: {}".format (ret))	# für log und debug
 
    myprint.myprint (DEBUG_LEVEL3, progname + "\nswi:Configdictionary after reading:")
    if (debug > 2):
        for x in cfglist_swi:
            print ("{} : {}".format (x, cfglist_swi[x]))
         
    if ret > 0 :

        print ("switcher3 terminate after configread")
        sys.exit(2)     # xxx   anpassen !!

    # wenn gpio blink angegeben ist (ungleich 0) starten wir den Blink Thread <<---

    try:
        gpio_blink =        int(cfglist_swi["gpio_blink"])
        wetter =            cfglist_swi["wetter"]
        testmode =          cfglist_swi["testmode"]
        debug_konf =        int(cfglist_swi["debug"])            # debug flag aus konfigfile
    except KeyError :
            myprint.myprint (DEBUG_LEVEL0, progname + "KeyError in cfglist_swi, check values!")   

    if debug_konf > 0:
        myprint.myprint (DEBUG_LEVEL0, progname + "debug verlangt in configfile, wert:{}".format(debug_konf))
    if debug == 0:                  # debug von Commendline param
        debug = debug_konf
    myprint.set_debug_level(debug)          # set level in the myPrint object


    # nicht schön, aber wir brauchens...
    testmodebol = False
    if testmode == "Ja":
        testmodebol = True
        myprint.myprint (DEBUG_LEVEL0, progname + "Testmode=Ja definiert in configfile !")


    # create instance of myBlink Class if pin is defined
    if (gpio_blink > 0):
        GPIO.setup(gpio_blink, GPIO.OUT)        # set GPIO Pin as output
        my_blink = myBlink(gpio_blink)          # create object
        my_blink.setDaemon (True)               # set to daemon, does not block termination    
        my_blink.start ()                       # start the thread, start blinking  
       


    #-----------------------------------
    # create Instance of MQTT-Conn Class  
    mymqtt = MQTT_Conn ( debug = debug, 
                        path = path, 
                        client = progname, 
                        ipadr = mqtt_broker_ip_cmdline, 
                        retry = retry, 
                        conf = path + "/" + configfile_name)    # creat instance, of Class MQTT_Conn  
    
    #------------------------------------
    #  create Instance of SwConnector Class  
    swconnector = SwConnector ( debug = debug, 
                                path = path,
                                configfile = configfile_name,
                                endpoint = 1,
                                mqtt_client = mymqtt,
                                callback = notifySwitcher)

    time.sleep(1)
    myprint.myprint (DEBUG_LEVEL0 ,progname +  "object created: {}".format(swconnector))

    #  Check connection status mqtt
    mqtt_connect, mqtt_error = swconnector.mqtt_status()
    #  returns mqtt_error = 128 if not connected to broker
    if mqtt_connect == True:
        myprint.myprint (DEBUG_LEVEL1, progname + "connected to mqtt broker")
         # subscribe to MQTT topics   
         #   do_subscribe()                           # doing subscribe
    else:
        # we are quitting if no connection
        # you could also try again later... 
        return (MQTT_ERROR)

    # wetter objekt erstellen,falls verlangt im config file
    if wetter == "Ja":                 # wetter ist verlangt, also kreiere instanz der Wetter  Klasse
        myprint.myprint (DEBUG_LEVEL0 ,progname +  "Wetter verlangt, also create wetter-object")
        my_wetter = Wetter (debug, path, mymqtt)               
                                         # suscriptions werden in der Klasse wetter gemacht 
                                         # 
    myprint.myprint (DEBUG_LEVEL0 ,progname +  "object created: {}".format(my_wetter))   

    #--------------------------------------
    # create Instance of SwHome Class  
    swhome = SwHome ( debug = debug, 
                        path = path, 
                        conf = path + "/" + configfile_name,    # creat instance, of Class MQTT_Conn     
                        test = testmodebol,
                        mqtt_client = mymqtt,
                        connector = swconnector
                        )

    time.sleep(0.5)
    #--------------------------------------
    # Create an instance of the sequencer 
    sequencer = MySequencer(    debug_in = debug, 
                                path_in = path,
                                conf = path + "/" + configfile_name,
                      #          callback1 = handle_sequencer)
                                callback1 = swhome)


        
    myprint.myprint (DEBUG_LEVEL1,  progname + "setup done, wait 1 sec.")

    myprint.myprint (DEBUG_LEVEL0 ,progname +  "object created: {}".format(sequencer))
    myprint.myprint (DEBUG_LEVEL0 ,progname +  "object created: {}".format(swhome))
    myprint.myprint (DEBUG_LEVEL0 ,progname +  "object created: {}".format(mymqtt))
    time.sleep(1)

    return(0)

#   end of setup function
#---------------------------------------------------------------    


#---------------------------------------------------------------
# main body of program
# #---------------------------------------------------------------
def runit():
    global   mqtt_connect, status_laueft_seit, time_old
    counter1 = 0
    counter2 = 0


    time_old = datetime.now()                           # fuer Zeitmessung
    # setup posit --------------
    try:
        
   #
        sequencer.daemon = True     # Don't let this thread block exiting.
        sequencer.start()           # start the sequencer
       
        myprint.myprint (DEBUG_LEVEL1 ,progname + "Start of switcher3 Main loop")

    #  ---- MAIN LOOP of program ---------------------------------    
        while True:
    #  ---- MAIN LOOP of program ---------------------------------
           
            if sequencer.is_alive():
                pass
            else:
                myprint.myprint (DEBUG_LEVEL0 ,progname + "Sequencer Thread is dead, siehe log")
                raise ThreadError               # sequencer lebt nicht mehr, hatte wohl execption
                                                    # wir müssen aufhören  
            time_new =  datetime.now() 
            time.sleep(2)

            status_laueft_seit = ( date.today() - start_switcher).days     # ermitteln, wieviele Tage der Switcher laeuft
#   check if alive meldung noetig
            
            delta = time_new - time_old
            delta = int(delta.days * 24 * 3600 + delta.seconds)     # delta in sekunden
            myprint.myprint (DEBUG_LEVEL3 ,progname +  "Check alive: delta(s): {}, laeuft seit Tagen: {}".format(delta,status_laueft_seit))
            if status_laueft_seit <= 2:                     # in den ersten 2 Tagen machen wir alle x min ein Eintrag
                if testmode == "Ja":
                    intervall = ALIVE_INTERVALL_0
                else:
                    intervall = ALIVE_INTERVALL_1
            else:                                   # nachher nur noch alle 24 Std
                intervall = ALIVE_INTERVALL_2
        
            if delta > intervall:              #   Zeit vorbei ?
	            time_old = datetime.now()
	            myprint.myprint (DEBUG_LEVEL0 ,progname +  "bin am leben..")

            # check mqtt Connection
           # check_mqtt()                    #   August 2025

        myprint.myprint (DEBUG_LEVEL2 ,progname + "end of big while")
        pass           
            

    #     END OF MAIN LOOP -------------------------------------------------
        
    except KeyboardInterrupt:
    # aufraeumem
        myprint.myprint (DEBUG_LEVEL0 ,progname +  "Keyboard Interrupt, alle Dosen OFF und clean up pins")
        error = 9
        term_verlangt = 1                       # signale to thread to stop
        if fortschritt > 0:
            swi_terminate(fortschritt)

    except ThreadError:     # error in thread sequencer
    # aufraeumem
        myprint.myprint (DEBUG_LEVEL0 ,progname + "Thread Error raised, wir müssen aufören")


    except Exception:
        #       etwas schlimmes ist passiert, wir loggen dies mit Methode myprint_exc der MyPrint Klasse
        myprint.myprint_exc ("init_switcher: etwas Schlimmes ist passiert.... !")
        error = 9
        term_verlangt = 1                       # signale to thread to stop
        if fortschritt > 0:
            swi_terminate(fortschritt)
    finally: 
    # hierher kommen wir immer, ob Keyboard Exception oder andere Exception oder keine Exception
        time.sleep(1)

        myprint.myprint (DEBUG_LEVEL0 ,progname +  "finally reached, alle Dosen off")	# wir starten       juni2018
       # return(error)
        swhome.all_off()
        myprint.myprint (DEBUG_LEVEL0 ,progname +  "TERMINATING")	# wir starten       juni2018
    #    swi_terminate (1)
        sys.exit(0)
    #

#---------------------------------------------------------------
# Program starts here
#---------------------------------------------------------------
if __name__ == "__main__":
    from sys import argv
   
    # do setup fuction
    general_error = setup()
    myprint.myprint (DEBUG_LEVEL0 ,progname +  "Setup returns errorcode:{}".format (general_error))
    if  general_error > 0:
        myprint.myprint (DEBUG_LEVEL0 ,progname +  "Quit wegen Fehler")
        sys.exit(2)                # terminate

    runit()             # run switcher3
    
   #------------------------------------------------ 