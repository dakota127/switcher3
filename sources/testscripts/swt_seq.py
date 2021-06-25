#!/usr/bin/python
# coding: utf-8
# ***********************************************************
#
# This is program ONE of a suite of two programs to demonstrate and test
# MQTT functionality on a Raspberry Pi
# Runs with Python3   and NOT tested under Python2 
# 
# This version of the program uses the  MQTT_Conn class tha encapsulates MQTT

# enhanced by Peter (Sept 2020)
# *********************************************************

import paho.mqtt.client as mqtt
import argparse, os, sys
import time
import threading
from sub.myprint import MyPrint             # Class MyPrint replace print, debug output
from sub.mymqtt import MQTT_Conn              # Class MQTT_Conn handles MQTT stuff
from sub.swc_sequencer import MySequencer              # Class Sequencer
from sub.myconfig import ConfigRead
import RPi.GPIO as GPIO                         #  Raspberry GPIO Pins




import json

# Define Variables
# parameter for callback from sequencer class
# values Parmameter1
ACTION_EVENT                = 1
ACTION_EVENT_FRAME1         = 1
ACTION_EVENT_FRAME2         = 2
TIME_OFDAY_EVENT            = 3   
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


DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
debug=0
terminate = False
what_to_do = 1                  # action 1

# instances of classes
myprint = None
swinterface= None
wait_time = 10
retry = False                   # do not retry on connect to brokaer
sequencer = None
zuhause = False            # nobody home
dosen=[]                        # list von Doseninstanzen
anz_dosen_config = 2
progname = "swt_seq"
logfile_name = "switcher3.log"
configfile_name = "swconfig.ini"
config_section = "switcher"                # look up values in this section
testmode=True              # aus Config File: Testmode Ja/Nein
fortschritt = 0
TRUEFALSE=[False,True]
are_actions_before_actual_time = True
term_verlangt = 0             # generelle term Variable, 1 heisst fuer alle Loops: beenden
reboot_verlangt = 0           # reboot Pi am Ende des Herunterfahrens von switcher

#   Struktur (Directory) der Daten, die aus dem Configfile swconfig.ini gelesen werden
# s  hier die defaultwerte der 'variablen'
cfglist_swi = {
        "testmode"          : "Nein",                         #
        "wetter"            : "Nein",                
        "gpio_blink"        : 5,
        "reserve"           : 'reservedefault'                 #
        }

# define Python user-defined exceptions
class Error(Exception):
    """Base class for other exceptions"""
    pass


class ThreadError(Error):
    """Raised when the input value is too small"""
    pass



#----------------------------------------------------
# Class Definition MyHome, erbt vom MyPrint
#----------------------------------------------------
class SwHomeDummy (MyPrint):
    ' klasse SwHome '


    def __init__(self, debug):  # Init Funktion
        self.errorcode = 8
        self.myprint (DEBUG_LEVEL1, "--> SwHomeDummy _init called")
        
    #---------------------------------------------------------------        
# function handle event from sequencer
#---------------------------------------------------------------
    def handle_sequencer_event (self, command):
        self.myprint (DEBUG_LEVEL1, "\t" + progname + "handle_sequencer_event called: {}/{}/{}/{}/{}/{}/{}". format(command[0],command[1],  \
                                                                                               command[2],command[3],command[4],command[5],command[6]   ))

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
def sigterm_handler(_signo, _stack_frame):
    global term_verlangt
    # Raises SystemExit(0):
    mypri.myprint (DEBUG_LEVEL0,  "SIGTERM/SIGHUP Signal received in switcher3")   # fuer Tests
    term_verlangt = 1
  #  terminate(9)                    #      alles gracefully beenden, dann fertig
    raise SystemExit(2)





#---------------------------------------------------------------       
# --- do subscribe and publish
# --- needs to be called after initial connection and after reconnect
#-------------------------------------------------------------       
def do_sub():
    return

#---------------------------------------------------------------
# handle incoming messages with MQTT_TOPIC_CMD
#---------------------------------------------------------------
def handle_sequencer (p1, p2,p3,p4,p5 ):
    global what_to_do, terminate , are_actions_before_actual_time

    print ("----> handle_sequencer called: {}/{}/{}/{}/{}". format(p1,p2,p3,p4,p5))
    if (p1 ==TIME_OFDAY_EVENT):
        print ("ist time of day event")
        if (p2 == ACTUAL_NOW):
            print ("time is now actual time")
            are_actions_before_actual_time = False
    else: 
        print ("ist action event") 



    
    ## thislist = list(("apple", "banana", "cherry")) # note the double round-brackets






#---------------------------------------------------------------
# Setup routine
# #---------------------------------------------------------------
def setup():
    global mymqtt, myprint, mqtt_connect, swhome, swinterface, sequencer
    
    print(progname + "started: {}".format(time.strftime('%X')))   
    argu()                          # get commandline argumants
    path = os.path.dirname(os.path.realpath(__file__))    # current path

    print ("Name logfile: {} ".format( path + "/" + logfile_name) )
    print ("Name configfile: {} ".format( path + "/" + configfile_name) ) 
     

    #Use BCM GPIO refernece instead of Pin numbers
    GPIO.setmode (GPIO.BCM)
    rev = GPIO.RPI_REVISION
 
    # create Instance of MyPrint Class 
    myprint = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  path + "/" + logfile_name ) 

    # Create Instance of the ConfigRead Class
    myconfig = ConfigRead(debug_level = debug)     

    myprint.myprint (DEBUG_LEVEL2, "\nswt_seq:Configdictionary before reading:")
    if (debug > 1):
        for x in cfglist_swi:
            print ("{} : {}".format (x, cfglist_swi[x]))

    # Read from Configfile  
    ret = myconfig.config_read (path + "/" + configfile_name ,config_section, cfglist_swi)  # call method config_read()

    myprint.myprint (DEBUG_LEVEL1,  "swt_seq:config_read() returnvalue: {}".format (ret))	# für log und debug
 
    myprint.myprint (DEBUG_LEVEL2, "\nswt_seq:Configdictionary after reading:")
    if (debug > 1):
        for x in cfglist_swi:
            print ("{} : {}".format (x, cfglist_swi[x]))
         
    if ret > 0 :
        sys.exit(2)     # xxx   anpassen !!

    swhome = SwHomeDummy (debug = debug)             # instance of dummy class swhome
        

    time.sleep(0.5)

    # Create instance of the sequencer 
    sequencer = MySequencer(    debug_in = debug, 
                                path_in = path,
                                conf = path + "/" + configfile_name,
                                callback1 = swhome)

    print ("swt_seq: Object created:{}".format(sequencer)) 

    
    time.sleep(3)

    return

#   end of setup function
#---------------------------------------------------------------    


#---------------------------------------------------------------
# main body of program
# #---------------------------------------------------------------
def runit():
    global   mqtt_connect
    counter1 = 0
    counter2 = 0

    # setup posit --------------
    try:
        
        sequencer.daemon = True  # Don't let this thread block exiting.
        sequencer.start()
       
        while True:
    #  ---- MAIN LOOP of program ---------------------------------
            while( True)  :       
                
                time.sleep(2)
         
                if sequencer.isAlive():
                    print ("main loop testseq")
                    pass
                else:
                    myprint.myprint (DEBUG_LEVEL0 ,"Sequencer Thread is dead, siehe log")
                    raise ThreadError               # sequencer lebt nicht mehr, hatte wohl execption
                                                    # wir müssen aufhören
          
                pass
            myprint.myprint (DEBUG_LEVEL2 ," end of big while")
        pass           
            

    #     END OF MAIN LOOP -------------------------------------------------
        
    except KeyboardInterrupt:
    # aufraeumem
        myprint.myprint (DEBUG_LEVEL0,  "swt_seq: Keyboard Interrupt")

        error = 9
        term_verlangt = 1                       # signale to thread to stop
     #   if fortschritt > 0:
      #      terminate(fortschritt)
    except ThreadError:   
    # aufraeumem
        myprint.myprint (DEBUG_LEVEL0 ,"swt_seq: Thread Error raised, wir müssen aufören")

    except Exception:
        #       etwas schlimmes ist passiert, wir loggen dies mit Methode myprint_exc der MyPrint Klasse
        myprint.myprint_exc ("swt_seq: etwas Schlimmes ist passiert.... !")
        error = 9
        term_verlangt = 1                       # signale to thread to stop
      #  if fortschritt > 0:
      #      terminate(fortschritt)
    finally: 
    # hierher kommen wir immer, ob Keyboard Exception oder andere Exception oder keine Exception
        time.sleep(1)

        myprint.myprint (DEBUG_LEVEL0,  "terminating swt_seq")	# wir starten       juni2018
       # return(error)
        sys.exit(0)
    #

#---------------------------------------------------------------
# Program starts here
#---------------------------------------------------------------
if __name__ == "__main__":
    from sys import argv
   
    setup()

    runit()
    
   #------------------------------------------------ 