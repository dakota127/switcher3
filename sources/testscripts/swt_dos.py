#!/usr/bin/python
# coding: utf-8
# ***********************************************
#   Schalten der Dosen  
#   
#   Testprogramm zum Testen und Schalten von 4 Dosen
#   instantiiert Klasse swDose 4 mal
#   
#   Juli 2018
#************************************************
#
import os
import sys
import time
from time import sleep
import argparse
from sys import version_info


from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.mymqtt import MQTT_Conn              # Class MQTT_Conn handles MQTT stuff
from sub.swc_dose import Dose                   # Class Dose, fuer das Dosenmanagement


DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

progname = "swt_dos"
logfile_name = "switcher3.log"
configfile_name = "swconfig.ini"

mymqtt  = None
dosen=[]        # list aller dosen
debug=1
counter=1       # loop counter
mypri=0
sleeptime=4
testmode = True

li_zimmer = ["zimmer-1", "zimmer-2", "zimmer-3", "zimmer-4", "zimmer-4",]

progname = "swt_dos "
logfile_name = "switcher3.log"
configfile_name = "swconfig.ini"
        
#----------------------------------------------------------
# get and parse commandline args
def argu():
    global testmode, counter
    global debug

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", help="kleiner debug", action='store_true')
    parser.add_argument("-D", help="grosser debug", action='store_true')
    parser.add_argument("-A", help="ganz grosser debug", action='store_true')
    parser.add_argument("-n", help="Testmode No", action='store_true')
    parser.add_argument("-l", help="Durchläufe", default=1, type=int)
    


    args = parser.parse_args()
#    print (args.d, args.s, args.dein, args.daus, args.dnor, args.dexc, args.dinc)          # initial debug
#    if args.s:
#        print ("s war hier")
    if args.d:
        debug=DEBUG_LEVEL1
    if args.D: 
        debug=DEBUG_LEVEL2
    if args.A: 
        debug=DEBUG_LEVEL3
    if args.n: 
        testmode = False   
    counter=args.l   
    return(args)
 

#---------------------------------------------------------------        
# handle callbacks from dosen  (called whenever a device switches)
#---------------------------------------------------------------
def handle_device_event (dose_list):
    mypri.myprint  (DEBUG_LEVEL0,  "\t" + progname + "handle_device_event called, dose_list:{}".format( dose_list)) 
        


#-----------------------------------------
def runit():

    global debug, mypri, mymqtt
    
    options=argu()        

    path = os.path.dirname(os.path.realpath(__file__))    # current path
   # create Instance of MyPrint Class 
    mypri = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  path + "/" + logfile_name )  


    mqtt_broker_ip_cmdline = ""
    retry = 0
    
   #-----------------------------------
    # create Instance of MQTT-Conn Class  
    mymqtt = MQTT_Conn ( debug = debug, 
                        path = path, 
                        client = progname, 
                        ipadr = mqtt_broker_ip_cmdline, 
                        retry = retry, 
                        conf = path + "/" + configfile_name)    # creat instance, of Class MQTT_Conn  


 #  Check connection status mqtt
    mqtt_connect, mqtt_error = mymqtt.get_status()           # get connection status
    #  returns mqtt_error = 128 if not connected to broker
    if mqtt_connect == True:
        mypri.myprint (DEBUG_LEVEL1, progname + "connected to mqtt broker")
         # subscribe to MQTT topics   
         #   do_subscribe()                           # doing subscribe
    else:
        mypri.myprint (DEBUG_LEVEL0, progname + "did NOT connect to mqtt broker, error: {}".format(self.mqtt_error))       
        # we are quitting if no connection
        # you could also try again later...
        mypri.myprint (DEBUG_LEVEL0, progname + "serious mqtt error,quit")           
        sys.exit(2)            
        
             #xxx
    # create instances of dosen class (5 stück) 
    try:
        dosen.append( Dose(1, testmode, debug, path+"/" + configfile_name , mqtt_connect, mymqtt, handle_device_event) )
        dosen.append( Dose(2, testmode, debug, path+"/" + configfile_name , mqtt_connect, mymqtt, handle_device_event) )
        dosen.append( Dose(3, testmode, debug, path+"/" + configfile_name , mqtt_connect, mymqtt, handle_device_event) )
        dosen.append( Dose(4, testmode, debug, path+"/" + configfile_name , mqtt_connect, mymqtt, handle_device_event) )
        dosen.append( Dose(5, testmode, debug, path+"/" + configfile_name , mqtt_connect, mymqtt, handle_device_event) )
    #    print (dosen)

        # setze fiktiver zimmer name für den test
        for i, dose in enumerate(dosen):
            dose.set_zimmer (li_zimmer[i])

        mypri.myprint (DEBUG_LEVEL0, "objects cerated:")
        for dose in dosen:
            mypri.myprint (DEBUG_LEVEL0, "{}".format(dose))
        for dose in dosen:
            mypri.myprint (DEBUG_LEVEL0, "{}".format(dose.show_status()))

        mypri.myprint (DEBUG_LEVEL0,  "dostest: ----------> Loop, Dosen {} mal ein/ausschalten". format(counter))	# für log und debug
    
        for i in range(counter):

            for i, dose in enumerate(dosen): 
                mypri.myprint (DEBUG_LEVEL0,  "dostest: Schalte Dose {} ein".format(i))	# für log und debug
                dose.set_auto(1)
                sleep(sleeptime)
                mypri.myprint (DEBUG_LEVEL0,  "dostest: Schalte Dose {} aus".format(i))	# für log und debug
                dose.set_auto(0)   
           
           

        mypri.myprint (DEBUG_LEVEL0,  "dostest: ----------> Loop beendet". format(counter))	# für log und debug
    
        
        mypri.myprint(DEBUG_LEVEL0,"dostest: ----------> Alle Dosen auf zuhause setzen")
        
        for dose in dosen:
            dose.set_zuhause()
    
        
        mypri.myprint (DEBUG_LEVEL0,  "dostest: ----------> Loop, Dosen Status ausgeben")	# für log und debug

        for dose in dosen:
            print ("Dosenstatus:{}".format(dose.show_status() ))
    

        mypri.myprint(DEBUG_LEVEL0,"dostest: ----------> Alle Dosen auf NICHT zuhause setzen")
        for dose in dosen:
            dose.set_nichtzuhause()
     
        anzahl_on = 0
        anzahl_off = 0
        print ("\nStatus der Dosen ausgeben:")
        for dose in dosen:
            stat = dose.show_status()
            print (stat) 
            anzahl_on = anzahl_on + stat[10]
            anzahl_off = anzahl_off + stat[11]
        print ("Schaltvorgänge total ON:{:05d}, OFF:{:05d}".format (anzahl_on, anzahl_off))
     
    except KeyboardInterrupt:
    # aufräumem
        mypri.myprint (DEBUG_LEVEL0,  "Keyboard Interrupt, alle Dosen OFF und clean up pins")
    except Exception:
        #       etwas schlimmes ist passiert, wir loggen dies mit Methode myprint_exc der MyPrint Klasse
        mypri.myprint_exc ("Etwas Schlimmes ist passiert.... !")
    finally:
    # hierher kommen wir immer, ob Keyboard Exception oder andere Exception
        mypri.myprint (DEBUG_LEVEL1, "Main Loop Ende erreicht ohne Probleme (finally reached)")
  #      print ("Dosen deleten")
  #      for dose in dosen:
  #          del dose
   
        pass            # letztes Statement im Main Loop    
        

#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
   


    if version_info[0] < 3:
        print ("swt_dos.py läuft nur richtig unter Python 3.x, du verwendest Python {}".format(version_info[0]))
        sys.exit(2)
   
    
    runit()
    
    mypri.myprint(DEBUG_LEVEL1,"Test beendet")

    sys.exit(0)
    
 #------------------------------------------------------------
    
