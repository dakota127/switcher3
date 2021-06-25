#!/usr/bin/python
# coding: utf-8
# ***********************************************************
# 	Programm zum Anzeigen des Inhalts der XML Steuerfiles
# 	Designed and written by Peter K. Boxler, Februar 2015  
# 
#   Hilfsprogramm, welches die Aktionen im Steuer-File detailliert anzeigt
#
#
#	Commandline Parameter
#	-d kleiner Debug, Statusmeldungen werden ausgegeben (stdout)
#	-D grosser Debug, es wird viel ausgegeben (stdout)
#
#   Verbessert/Erweitert im Januar 2015, Peter K. Boxler
#   Verbessert/Erweitert im Juli 2018, Peter K. Boxler

# ***** Imports ******************************
import sys, getopt, os
import time
from time import sleep
import datetime
import argparse
from sub.swcfg_switcher import cfglist_swi
from sub.swcfg_switcher import cfglist_akt       # struktur des Aktors Config im Config File  
from sub.swc_dose import Dose                   # Class Dose, für das Dosenmanagement
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.myconfig import ConfigRead

from sub.configread_dosen import read_dosenconfig
from sub.configread_dosen import write_dosenconfig

from sub.swcfg_switcher import cfglist_swi
from sub.swcfg_switcher import cfglist_akt       # struktur des Aktors Config im Config File  


# ***** Variables *****************************
tmp=0				# tmp für ein/aus

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
debug=0
#
progname = "testconfig"
logfile_name = "switcher3.log"
configfile_name = "swconfig.ini"
dosenconfig = "swdosen.ini"
config_section = "switcher"                # look up values in this section

# ***** Function Parse commandline arguments ***********************

#----------------------------------------------------------
# get and parse commandline args
def argu():
    global debug

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", help="kleiner debug", action='store_true')
    parser.add_argument("-D", help="grosser debug", action='store_true')
    parser.add_argument("-A", help="ganz grosser debug", action='store_true')


    args = parser.parse_args()
    if args.d:
        debug=DEBUG_LEVEL1
    if args.D: 
        debug=DEBUG_LEVEL2
    if args.A: 
        debug=DEBUG_LEVEL3
                 
    return(args)
    

def fun1():
    mypri.myprint (DEBUG_LEVEL0,  "Function fun1 prints...")	# für log und debug
    
def fun2(callback):
    mypri.myprint (DEBUG_LEVEL0,  "bin in fun2 vor call to callback")	# für log und debug

    callback()
    mypri.myprint (DEBUG_LEVEL0,  "bin in fun2 nach call to callback")	# für log und debug
    


# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    options=argu()                          # get commandline args
    
     #   Etablieren des Pfads 
    path=os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft


   # create Instance of MyPrint Class 
    mypri = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  path + "/" + logfile_name ) 



    # Create Instance of the ConfigRead Class
    myconfig = ConfigRead(debug_level = debug)     
   

# Read from Configfile  
    ret = myconfig.config_read (path + "/" + configfile_name ,config_section, cfglist_swi)  # call method config_read()

    mypri.myprint (DEBUG_LEVEL1,  "config_read() returnvalue: {}".format (ret))	# für log und debug
 
    mypri.myprint (DEBUG_LEVEL2, "\nConfigdictionary after reading:")
    if (debug > 1):
        for x in cfglist_swi:
            print ("{} : {}".format (x, cfglist_swi[x]))

# suche selbst nach werten, gibt aber exception, wenn nicht gefunden    
    for x in cfglist_swi:
            print ("{} : {}".format (x, cfglist_swi[x]))


    

  
   
    mypri.myprint (DEBUG_LEVEL0,  "Nun actor_1 config lesen")	# für log und debug

# Read from Configfile  
    ret = myconfig.config_read (path + "/" + configfile_name ,"aktor_1", cfglist_akt)  # call method config_read()


    mypri.myprint (DEBUG_LEVEL0,  "config_read bringt: {}".format (ret))	# für log und debug
    if ret > 0:
        sys.exit(2)
    

    if (debug > 1):
        for x in cfglist_akt:
            print ("{} : {}".format (x, cfglist_akt[x]))



    mypri.myprint (DEBUG_LEVEL0,  "Nun actor_5 config lesen")	# für log und debug  
    #Read from Configfile  
    ret = myconfig.config_read (path + "/" + configfile_name ,"aktor_5", cfglist_akt)  # call method config_read()

    mypri.myprint (DEBUG_LEVEL0,  "config_read bringt: {}".format (ret))	# für log und debug
    if ret > 0:
        sys.exit(2)  

    if (debug > 1):
        for x in cfglist_akt:
            print ("{} : {}".format (x, cfglist_akt[x]))


    mypri.myprint (DEBUG_LEVEL0,  "\nnun test mit lesen swdosen.ini file")
    
    dosenconfig_file = path + "/"+ dosenconfig
    anz_dosen_config = read_dosenconfig (dosenconfig_file, mypri.myprint ,debug)

        
    mypri.myprint (DEBUG_LEVEL0,  "Anzahl Dosen konfiguriert in swdosen.ini: {}". format(anz_dosen_config))         
           
    mypri.myprint (DEBUG_LEVEL0,  "\nnun test mit schreiben swdosen.ini file")
    
    write_dosenconfig (dosenconfig_file, mypri.myprint , int(4), debug)
    
   
# fertig behandlung confifile

    mypri.myprint (DEBUG_LEVEL0,  "\nam Schluss a simple test with function calls")
# noch test funktionsaufruf mit callback, ich rufe fun2 auf mit Parameter fun1 und fun2 führt dies aus. Genial.
    aa=fun1             # aa points to fun1()
    fun2(aa)            # an fun2 gebe ich fun1() als parameter
    


#  Abschlussvearbeitung
    print ("\nProgram terminated....")
    sys.exit(0)
#**************************************************************
#  That is the end
#***************************************************************
#