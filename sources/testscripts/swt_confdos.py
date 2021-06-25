#!/usr/bin/python
# coding: utf-8

# ---------------------------------------------------
# swt_log.py Testprogramm für Class SWDos_conf
#  reaa and updated swdosen.ini  (Configfile Anzahl Dosen)
#----------------------------------------------------
#
import sys, getopt, os
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.swc_dosconf import SWDos_conf
import argparse

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

# instances of classes
myprint     = None
swdosconf = None
path = ""
anzahl_schreiben = 0
progname = "swt_confdos "
logfile_name = "switcher3.log"


#----------------------------------------------------------
# get and parse commandline args
def argu():
    global debug, anzahl_schreiben
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", help="kleiner debug", action='store_true')
    parser.add_argument("-D", help="grosser debug", action='store_true')
    parser.add_argument("-A", help="ganz grosser debug", action='store_true')
    parser.add_argument("-n", help="Anzahl Dosen schreiben", default=0, type=int)


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
    print (args.n)
    if args.n > 0 :
        anzahl_schreiben = args.n
        if anzahl_schreiben > 9:             # setze upper limit
            anzahl_schreiben =9

    return(args)
    

#--------------------------------------------
#  Function runit
#--------------------------------------------
def runit():
    global path, myprint

    print ()
    debug = DEBUG_LEVEL2

    path = os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft

# create Instance of MyPrint Class 
    myprint = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  path + "/" + logfile_name ) 
  

    myprint.myprint (DEBUG_LEVEL0, "Testprogramm to test dosenconfig")

    swdosconf = SWDos_conf (debug = debug, path = path)   # instanz der Klasse erstellen


    myprint.myprint (DEBUG_LEVEL0 ,progname +  "object created: {}".format(swdosconf))

    zahl = swdosconf.read_dosenconfig()
    print ("Gelesen Anzahl Dosen:{}".format(zahl))
#
    print ("Schreiben Anzahl:{}".format(anzahl_schreiben))
    ret = swdosconf.write_dosenconfig(anzahl_schreiben)
    if ret == 0:                    # zero means : anzahl war schon wie gehabt, wurde nichts verändert 
        error_text_1 = "Anzahl nicht verändert"
    else:
        error_text_1 = "Neue Anzahl: {}".format (ret)
    print (error_text_1)
    return


#-----------------------------------
# MAIN, starts here
#------------------------------------
if __name__ == "__main__":
    argu()
    runit()

print ("\nProgramm fertig")
#----------------------------