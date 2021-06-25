#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class SWDos_conf 
#   
#   Diese Class kapselt den Config-File für die Anzahl Dosen
#
#   diese Class erbt von der MyPrint Class
#   
#   Feb 2021 
#************************************************
#
import os
import sys
import time
from time import sleep
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from configparser import SafeConfigParser
from datetime import date, datetime


DEBUG_LEVEL0=0                      
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
home_button  = 13
home_led = 6
parser = 0



progname = "swc_dosconf "
configfile_name = "swdosen.ini"  # config file enthaltend anzahl dosen


#----------------------------------------------------
# Class Definition SWDos_conf, erbt vom MyPrint
#----------------------------------------------------
class SWDos_conf (MyPrint):
    ' klasse SWDos_conf '


    #----------------------------------------------------
    # Construktor
    #----------------------------------------------------
    def __init__(self, debug, path):  # Init Funktion
        self.errorcode = 0
        self.debug = debug
        self.path = path
        self.myprint (DEBUG_LEVEL1, progname + "_init called")


    #-------------------------------------------
    # __repr__ function SwHome
    # 
    def __repr__ (self):

        rep = "SWDos_conf ()"
        return (rep)


    #----------------------------------------------------
    # Method read_dosenconfig
    #----------------------------------------------------
    # hier wird der file swdosen.ini gelsen und die dort gespeicherte Anzahl Dosen zurückgegeben
    # neu im Januar 2019
    def read_dosenconfig (self):
        global parser
        found = False
        self.myprint (DEBUG_LEVEL2, progname + "--> read_dosenconfig called")
        parser = SafeConfigParser()         # eine Instanz der Klasse SafeConfigParser machen
        try:                                # prüfen, ob der File schon existiert
            fp = open(configfile_name)
            ret = parser.readfp (fp) 
            if parser.has_section("anzdosen"):     # sektion vorhanden ?

                for name, value in parser.items("anzdosen"):   # returns a list of tuples containing the name-value pairs.
                    if self.debug > DEBUG_LEVEL2:
                        print ("Name: {}  Value: {} ".format(name, value))
                    if name == "anzahl":
                        dosen= int(value)               # entnehme die anzahl
                        found = True     
                fp.close()                      # close file           
            else:
                self.myprint (DEBUG_LEVEL0, progname + "Abschnitt {} fehlt in Configfile {}".format("anzdosen","swdosen.ini"))  
        
            self.myprint (DEBUG_LEVEL0, progname + "Dosen anzahl gefunden: {}".format(dosen))
        except FileNotFoundError:
            self.myprint (DEBUG_LEVEL0, progname + "File swdosen.ini nicht gefunden")

        if found == True:
            pass
        else:
            self.myprint (DEBUG_LEVEL0, progname + "nehme defaultwert 4 dosen")
            dosen = 4        

        return (dosen)

    #----------------------------------------------------
    # Method read_dosenconfig
    #----------------------------------------------------
    # write file dosenconfig--------------- 
    # er wird der config-File dosen.ini jedesmal neu geschrieben, er enthält nur eine Sektion mit zwei tuples 
    # neu im Januar 2019
    def write_dosenconfig (self, neue_anzahl):
        dosen= 99                   # default wert bei not found
        found = False
        self.myprint (DEBUG_LEVEL0, progname + "--> write_dosenconfig {} called".format (neue_anzahl))
    #  erst alle Werte im config löschen, damit nur die neuen Tuple geschrieben werden.
    
        for section in parser.sections():
            parser.remove_section(section)
   
        try:                                # prüfen, ob der File schon existiert
            fp = open(configfile_name)
            ret=parser.readfp (fp) 
            if parser.has_section("anzdosen"):     # sektion vorhanden ?

                for name, value in parser.items("anzdosen"):   # returns a list of tuples containing the name-value pairs.
                    if self.debug > DEBUG_LEVEL2:
                        print ("Name: {}  Value: {} ".format(name, value))
                    if name == "anzahl":
                        dosen= int(value)               # entnehme die anzahl
                        found = True     
                fp.close()                      # close file           
            else:
                self.myprint (DEBUG_LEVEL0, progname + "Abschnitt {} fehlt in Configfile {}".format("anzdosen","swdosen.ini"))  
        
            self.myprint (DEBUG_LEVEL1, progname + "Dosen anzahl gefunden: {}".format(dosen))
        except FileNotFoundError:
            self.myprint (DEBUG_LEVEL0, progname + "File swdosen.ini nicht gefunden, wird neu erstellt")

        self.myprint (DEBUG_LEVEL0, progname + " write_value found: {} gefunden. {} neu: {}". format (found, dosen, str(neue_anzahl)))

        if (dosen != neue_anzahl):
    
        # zuerst alle Werte im config löschen, damit nur die neuen Tuple geschrieben werden.
            self.myprint (DEBUG_LEVEL2, progname +  "write_value nun schreiben")       
            for section in parser.sections():
                parser.remove_section(section)

            cfgfile = open(configfile_name,'w')

            parser.add_section('anzdosen')
            parser.set('anzdosen', 'anzahl', str(neue_anzahl)) 
            parser.set('anzdosen', 'written', str(datetime.now()))

    # writing our configuration file to 'swdosen.ini'
            parser.write(cfgfile)
            cfgfile.close()
            self.myprint (DEBUG_LEVEL0, progname + "write file swdosen.ini geschrieben, Anzahl: {}".format(str(neue_anzahl))) 
        else:
            neue_anzahl = 0
            self.myprint (DEBUG_LEVEL0, progname + "anzahl dosen identisch, also nichts schreiben")

        return (neue_anzahl)

# --------------------------

            
# *************************************************
# Program starts here
# *************************************************

# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swc_dosconf.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
#**************************************************************
#  That is the end
#***************************************************************
#