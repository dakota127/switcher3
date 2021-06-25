#!/usr/bin/python
# coding: utf-8
# ***********************************************************
#   Testscript for class MyPrint
#   This program is using the class MyPrint
# 
#   It demonstrates how to replace the commonly used print() statement
#   with something much more elaborate.
#   Depending on the DEBUG_LEVEL set through a commandline argument
#   more or less debug output is written to the screen and AT THE SAME Time
#   written to log file.
#   The name of the log files can be specified when an instance of the
#   MyPrint calss is instantieted.
#
#   The logfile is an Rotating File with max three files. 
# ***** Imports ******************************
import sys, getopt, os
import time
import argparse
import datetime

import socket               # just for testing
import locale

from sub.myprint import MyPrint              # Class MyPrint for printing an logging printing

# ***** Variables *****************************

DEBUG_LEVEL0 = 0
DEBUG_LEVEL1 = 1
DEBUG_LEVEL2 = 2
DEBUG_LEVEL3 = 3

debug=DEBUG_LEVEL0

progname = "printest_1"
logfile_name = "switcher3.log"


#
# ***** Function Parse commandline arguments ***********************
# get and parse commandline args
def argu():
    global li 
    global seas
    global debug

    parser = argparse.ArgumentParser()
                                                                             # kein Parm  only see DEBUG_LEVEL0                  
    parser.add_argument("-d", help="minimal debug", action='store_true')      # see also DEBUG_LEVEL1
    parser.add_argument("-D", help="more debug ", action='store_true')        # see also DEBUG_LEVEL2 
    parser.add_argument("-A", help="even more debug", action='store_true')    # see also DEBUG_LEVEL3 
                                                              
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
                 
    return(args)
    
	
# ***********************************************

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

#-------------------------------------------------
# funktion testprint zum Testen der debug-print funktion
#------------------------------------------------
def test_print():
    global debug
    
    
 # first try: debug level set to zero   
    mypr.myprint(DEBUG_LEVEL0,"---> Debug-Level is set to {}".format( debug))
  
    mypr.myprint(DEBUG_LEVEL0, "Debug-Output Level {} very important".format(DEBUG_LEVEL0))    # unwichtig
    mypr.myprint(DEBUG_LEVEL1, "Debug-Output Level {} important".format(DEBUG_LEVEL1))    # weniger wichtig
    mypr.myprint(DEBUG_LEVEL2, "Debug-Output Level {} less important".format(DEBUG_LEVEL2))    # wichtig
    mypr.myprint(DEBUG_LEVEL3, "Debug-Output Level {} not important".format( DEBUG_LEVEL3))    # sehr wichtig
    
    print (" ")         # do some newline stuff
    print (" ")
    print (" ")
 # first try: debug level set to 2   execute the same statements
    debug=2
    mypr.set_debug_level (debug)
    mypr.myprint(DEBUG_LEVEL0,"---> Debug-Level now set to {}".format( debug))
  
    mypr.myprint(DEBUG_LEVEL0, "Debug-Output Level {} sehr wichtig ".format(DEBUG_LEVEL0))    # unwichtig
    mypr.myprint(DEBUG_LEVEL1, "Debug-Output Level {} wichtig".format(DEBUG_LEVEL1))    # weniger wichtig
    mypr.myprint(DEBUG_LEVEL2, "Debug-Output Level {} weniger wichtig".format(DEBUG_LEVEL2))    # wichtig
    mypr.myprint(DEBUG_LEVEL3, "Debug-Output Level {} unwichtig".format( DEBUG_LEVEL3))    # sehr wichtig


    print ("\nEnde Debug-Print")
#

# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    options=argu()          # get commandline args  
   # locale.setlocale(locale.LC_ALL, 'de_DE')

   
    try:
        locale.setlocale(locale.LC_TIME , 'de_CH')
    except:
        print ("setzen Locale geht nicht, prüfe mit Befehl locale -a ")
    start_time = datetime.datetime.now()
    
    print ("Startzeit:{}".format(start_time.strftime("%A, %d %B %Y : %H:%M:%S" )))
 #   Etablieren des Pfads 
    path=os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft
     # create Instance of MyPrint Class 
    mypr = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  path + "/" + logfile_name ) 



    mypr.myprint(DEBUG_LEVEL3,"Start printest_1")

    ipadr=get_ip()                # do get ip adr first
    mypr.myprint(DEBUG_LEVEL0,"This Pi's IP-Adress: {}".format(ipadr))

    test_print()        # do the work
    
    #------------------------------
    # do list clone
    print ("Now try to clone a list---")

    # Python program to copy or clone a list
    # Using the Slice Operator
    def Cloning(li1):
        li_copy = li1[:]
        return li_copy
  
# Driver Code
    li1 = [
        ["aaa", "4"],
        ["bbb", "34"],
        ["ccc", "234"]
        ]


    li2 = Cloning(li1)
    print("Original List:", li1)
    print("After Cloning:", li2)
    
    sys.exit(0)
#**************************************************************
#  That is the end
#***************************************************************
#