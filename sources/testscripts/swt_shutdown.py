#!/usr/bin/python
# coding: utf-8
# ***********************************************************
# 	Programm zum Testen des shutdowns
# 

#   
#-------------------------------------------------
#
import sys, os
from time import sleep
from datetime import date, datetime, timedelta
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

myprint = None

debug=1

progname = "swt_shutdown "
logfile_name = "switcher3.log"

#--------------------------------------------------    
def runit():

    path = os.path.dirname(os.path.realpath(__file__))    # current path
   # create Instance of MyPrint Class 
    myprint = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  path + "/" + logfile_name )  
    try:
        myprint.myprint (DEBUG_LEVEL0, progname + "doing os command..")
        cmd = "sudo systemctl stop switcher3.service"           # stop switcher3 service
        ret = os.system("sudo systemctl stop switcher3.service")
        myprint.myprint (DEBUG_LEVEL0, progname + "return from os command: {}".format(ret))
        sleep(15)                                           # braucht zeit bis alle dosen off
    # hier reboot thread benachrichtigen
   
    except Exception:
        #       etwas schlimmes ist passiert
            myprint.myprint_exc ("swt_shutdown: etwas Schlimmes ist passiert.... !")
    
    finally:
        myprint.myprint (DEBUG_LEVEL0, progname + "finally reached, doing shutdown")
        os.system('sudo shutdown -h now')   
    
    sys.exit(0)
    

# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    runit()
    
 #---------------------------------------------
 #
    