#!/usr/bin/python
# coding: utf-8
# ***********************************************************
# 	Programm zum Anzeigen des Inhalts der XML Steuerfiles
# 	Designed and written by Peter K. Boxler, Februar 2015  
# 
#   new version Feb 2021
#   Hilfsprogramm, welches die Aktionen im Steuer-File detailliert anzeigt
#
#
#	Commandline Parameter
#	-d kleiner Debug, Statusmeldungen werden ausgegeben (stdout)
#	-D grosser Debug, es wird viel ausgegeben (stdout)
#
#   Verbessert/Erweitert im Januar 2015, Peter K. Boxler
#   Verbessert/Erweitert im Juli 2018, Peter K. Boxler
#   reduced for watering project Sept 2020
# ***** Imports ******************************
import os, sys
from xml.dom import minidom

from sub.swc_actionlist import ActionList
import argparse
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.myconfig import ConfigRead
from sys import version_info

forep=1

onoff={1:'ON', 0:'OFF'}
seas=0
#--------------------------------------------------------------------
# vom Parser werden 3 Listen erstellt aufgrund der Daten im XML File

# list_tage[] ist Liste über alle Aktionen pro Wochentag, chronologisch
# dise Liste wird von Sequencer abgearbeitet
list_tage= [ [] for z in range (7)]            # list has 7 members: one for every day of the week
  

# 
# list_device:  Liste über alle Tage, pro Tag alle devices und pro device alle aktionen 
#   WICHTIG:    diese Liste wird nur aufgebaut, damit swlist_action eine Liste über alle Dosen erstellen kann.<<-----------------
#               switcher3.py braucht diese Liste nicht.
list_device= [ [] for z in range (7)]          # list has 7 members: one for every day of the week                                

# Lisre aller Namen der Zimmer
list_zimmer =[]
#-------------------------------------------------------------------

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
debug=0

progname = "swlist3"
logfile_name = "switcher3.log"
configfile_name = "swconfig.ini"
config_section = "switcher"                # look up values in this section

# ***** Variables *****************************
#   Struktur (Liste) der Daten, die aus dem Configfile swconfig.ini gelesen werden
# s  hier die defaultwerte der 'variablen'
cfglist_seq = {
        "xmlfile_prefix"        : "swhaus1",
        "ctrl_file"             : "test_1",
        "adjust_needed"         : 1,
        "start_limit"           : "22.00",

}



#
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
    

#----------------------------------------------
def ausgabe_liste():
# was solen wir ausgeben?  
#
 
    actionList.print_actions(list_tage,list_device,list_zimmer)	    # alle gefundenen aktionen in Listen ausgeben
#
  


# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#


    if version_info[0] < 3:
        print("swlist3.py läuft nur richtig unter Python 3.x, du verwendest Python {}".format(version_info[0]))
        sys.exit(2)

    options=argu()        
 #   Etablieren des Pfads 
    pfad = os.path.dirname(os.path.realpath(__file__))    # current path

    print ("Name logfile: {} ".format( pfad + "/" + logfile_name) )
    print ("Name configfile: {} ".format( pfad + "/" + configfile_name) ) 
     

 
    # create Instance of MyPrint Class 
    myprint = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  pfad + "/" + logfile_name ) 

    
    
     # Create Instance of the ConfigRead Class
    myconfig = ConfigRead(debug_level = debug)     
                                                    # übergebe appname und logfilename


    actionList = ActionList(debug,pfad)      # Instanz der actionLister Class

    configfile=pfad + "/swconfig.ini"
    # ret=config.config_read(configfile,"watering",cfglist_swi)
     # we use the configfile given by switcher, could also use our own
    ret = myconfig.config_read (configfile ,"sequencer", cfglist_seq)  # call method config_read()
    if ret > 0:
        print("swlist3: config_read hat retcode: {}".format (ret))
        sys.exit(2)

    myprint.myprint (DEBUG_LEVEL2, "\nConfigdictionary after reading:")
    if (debug > 1):
        for x in cfglist_seq:
            print ("{} : {}".format (x, cfglist_seq[x])) 
# fertig behandlung confifile
# Einlesen und Parsen der Steuer-Files für alle Seasons             alles neu juni2018
    ret, file_id  = actionList.get_actionList (list_tage,list_device, list_zimmer,cfglist_seq)
#
#   nun sind alle Aktionen aus den XML-Files eingelesen und versorgt in den Listen list_tage, list_device und zimmer
#
#   print what we got back from actionList Class
    if (debug > 2):
        print ("\nswlist3.py: got these lists from class actionList: <-----------------")
     
        # print all days and actions
        print ("Anzahl Tage gefunden: {}".format(len(list_tage)))
        for v , tag in enumerate(self.list_tage):
            print ("Tag: {}".format(v))
            for action in self.list_tage[i][y]:
                    print ("action:{}".format(action))

        # print all devices and all days and all actions
        print ("\nAnzahl Dosen gefunden: {}".format(len(list_device)))
        for i, dose in enumerate (list_device):     
            print ("Device: {}".format(i))

            for y, tag in enumerate (dose):
                print ("Tag: {}".format(y))

                for action in tag:
                    print ("action:{}".format(action))
            

        # print alle gefundenen Zimmer
        print (" ")
        print (list_zimmer)
        print (" ")

    if ret > 0:
        print ("Methode get_files bringt errorcode: {}, kann nicht weiterfahren".format(ret))
    else:
    
# Anzahl Dosen feststellen: loop über alle Tage und schauen, wo maximum ist
        anz_devices=0
        for y in range (len(list_device)):
            for i in range (len(list_device[0])):
                anz= (len(list_device[0][i]))
                if (anz >  anz_devices): anz_devices=anz
        anz_devices -= 1      # liste hat 5 elemente , es gibt aber -1 dosen
        print ("swlist3: es wurden maximal {} Devices gefunden".format( anz_devices))
#        
        ausgabe_liste()  # lokale Funktion, keine Parameter 
  
#  Abschlussvearbeitung
    print ("\nProgram terminated....")
    sys.exit(0)
#**************************************************************
#  That is the end
#***************************************************************
#