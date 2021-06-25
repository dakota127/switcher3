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
#  contains a bad error to show functionality
#
#   The logfile is an Rotating File with max three files. 
# ***** Imports ******************************
import os, sys
import argparse

from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output


#
DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
debug=0
#
progname = "printest_1"
logfile_name = "switcher3.log"
# ***** Function Parse commandline arguments ***********************

#----------------------------------------------------------
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

    if args.d:
        debug=DEBUG_LEVEL1
    if args.D: 
        debug=DEBUG_LEVEL2
    if args.A: 
        debug=DEBUG_LEVEL3
        
    return(args)
    
#----------------------------------------------


# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    nummer=[2,3]                # for testen
    options=argu()              # get commandline args 
    
   #   Etablieren des Pfads 
    path=os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft
     # create Instance of MyPrint Class 
    mypri = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  path + "/" + logfile_name ) 


    mypri.myprint(DEBUG_LEVEL0, "Start program printest")
    mypri.myprint(DEBUG_LEVEL1, "another log_entry")
    mypri.myprint(DEBUG_LEVEL1, "yet another logentry")

    try:                                                       # übergebe appname und logfilename
        mypri.myprint (DEBUG_LEVEL1, "working")
        mypri.myprint (DEBUG_LEVEL2, "hard working")
        mypri.myprint (DEBUG_LEVEL3, "terribly hard working")
        pass
 #       qw=zuu
        nummer[4]=23            # this is to create a serious error within Python 
    except Exception:
                   
        mypri.myprint_exc ("Something bad happened.... !")
    finally:
        mypri.myprint (DEBUG_LEVEL1, "finally reached")
        
# fertig behandlung confifile
# Einlesen und Parsen der Steuer-Files für alle Seasons             alles neu juni2018

#  Abschlussvearbeitung
    print ("\nProgram terminated....")
    
    sys.exit(0)
#**************************************************************
#  That is the end
#***************************************************************
#