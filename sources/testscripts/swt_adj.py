#!/usr/bin/python
# coding: utf-8
# ***********************************************************
#   Testscript timetest
#
#   probieren der time, differenz und so 
# ***** Imports ******************************
import sys, getopt, os
import time
import argparse
import datetime      
from datetime import date, datetime, timedelta
from operator import itemgetter
import sub.swc_adjust
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output



# ***** Variables *****************************

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

debug=DEBUG_LEVEL0
start_time_str =0
start_time =0
start_day =0
timenow=0
actioncalc = None
debug = 0
allweeks = False

logfile_name = "switcher3.log"
progname = "swt_adj"

actionList = [ 
                ["21.15",1275,30,"21.15",1,1],
                ["21.45",1305,30,"21.45",1,0],
                ["21.35",0,0,"21.35",1,1],
                ["21.55",0,0,"21.55",1,0],
                ["22.10",0,0,"22.10",2,1],
                ["23.20",0,0,"23.20",3,0],
                ["23.10",0,0,"23.10",4,1],
                ["23.20",0,0,"23.20",4,0],
                ["01.10",0,0,"01.10",1,1],
                ["01.20",0,0,"01.20",1,0],
                ["05.20",0,0,"05.20",2,1],
                ["06.20",0,0,"06.20",2,0],
            ]
        
#
# ***** Function Parse commandline arguments ***********************
# get and parse commandline args
def argu():
    global li 
    global seas
    global debug, allweeks

    parser = argparse.ArgumentParser()
                                                          #       kein Parm       will DEBUG_LEVEL0 sehen (sehr wichtig)                   
    parser.add_argument("-d", help="kleiner debug", action='store_true')        # will DEBUG_LEVEL1 sehen
    parser.add_argument("-D", help="grosser debug", action='store_true')        # will DEBUG_LEVEL2 sehen
    parser.add_argument("-A", help="ganz grosser debug", action='store_true')   # will DEBUG_LEVEL3 sehen
    parser.add_argument("-w", help="allweeks", action='store_true')
                                                              
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
    if args.w:
        allweeks = True
                 
    return(args)
    
	
# ***********************************************


#  ---------------------------------------------------------------------------------------
#--Private  Funktion convert time  given ist switchtime in minutes of the day
#  ---------------------------------------------------------------------------------------
def convTime(min_in):
          
    c = min_in % 60         # c reminder is minutes  
    b = (min_in - c) // 60  # calc hour of the day
      
    f = str(c)
    e = str(b)
    if c < 10: f = "0" + str(c)
    if b < 10: e = "0" + str(b)
    return (e + "." + f)        # format "hh.mm"


#–---------------------------------------------
# setup()
def setup():
    global actioncalc, myprint

    today = datetime.now()
    week = int(today.strftime("%V"))
    print ("weeky of year:{}".format(week))

    path = os.path.dirname(os.path.realpath(__file__))    # current path
# create Instance of MyPrint Class 
    myprint = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  path + "/" + logfile_name ) 
    actioncalc = sub.swc_adjust.CalcAdjust (debug,allweeks)     # instanz von CalcAdjust erstellen 

    actioncalc._calc_base(0)



# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    options=argu()        
    setup()
    # this test programm performs two tests:

    # here the defined actions are processed
    if allweeks == False:  
        myprint.myprint (DEBUG_LEVEL1, "\nAdjust actions")  
        for action in actionList:
            
            new_action, minutes = actioncalc.calc_adjusttime (action , 0)
            print ("test new action   :   {}".format(new_action))
    
    # here we run over all weeks of the year an show the adjust minutes for every week
    else:
        myprint.myprint (DEBUG_LEVEL1, progname + "\nLaufe über alle Wochen des Jahres")
        for we in range (1,52,1):
            new_action, minutes = actioncalc.calc_adjusttime (actionList[0] , we)           # use first element
            newtime = convTime (1319 - minutes)
            print ("week: {:2}, adjust: {:3}  new time: {} (from 21.59)".format(we, minutes, newtime))
    
    sys.exit(0)
#**************************************************************
#  That is the end
#***************************************************************
#