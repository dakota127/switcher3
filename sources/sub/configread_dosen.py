#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class ConfigRead 
#   
#   zum Lesen eines Config Files im Format .ini
#
#   diese Class erbt von der MyPrint Class
#
#   stellt eine einzige public method config_read zur Verfügung
#   mit welcher Configfiles gelesen und geparst werden können
#   Input Parm ist eine List, welche die Namen/Wert Paare enthält
#   Dise Paare müssen auch im Konfig File vorkommen in einer bestimmten Sektion
#
#   Es gibt auch ein Test-Programm testconfig.py für Tests
#
#   August 2018, Peter K. Boxler
#
## ***** Imports ******************************
import sys, getopt, os
from configparser import SafeConfigParser
from datetime import date, datetime
# ***** Konstanten *****************************

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
#

parser = 0


#--- ---------------------------- 
#     
# hier wird der file swdosen.ini gelsen und die dort gespeicherte Anzahl Dosen zurückgegeben
# neu im Januar 2019
def read_dosenconfig (filename,myprint,debug):
    global parser
    found = False
    myprint (DEBUG_LEVEL2,"--> read_dosenconfig called")
    parser = SafeConfigParser()         # eine Instanz der Klasse SafeConfigParser machen
    try:                                # prüfen, ob der File schon existiert
        fp = open(filename)
        ret = parser.readfp (fp) 
        if parser.has_section("anzdosen"):     # sektion vorhanden ?

            for name, value in parser.items("anzdosen"):   # returns a list of tuples containing the name-value pairs.
                if debug > DEBUG_LEVEL2:
                    print ("Name: {}  Value: {} ".format(name, value))
                if name == "anzahl":
                    dosen= int(value)               # entnehme die anzahl
                    found = True     
            fp.close()                      # close file           
        else:
            myprint (DEBUG_LEVEL0,"read_dosenconfig Abschnitt {} fehlt in Configfile {}".format("anzdosen","swdosen.ini"))  
        
        myprint (DEBUG_LEVEL2,"Dosen anzahl gefunden: {}".format(dosen))
    except FileNotFoundError:
        myprint(DEBUG_LEVEL0,"File swdosen.ini nicht gefunden")

    if found == True:
        myprint(DEBUG_LEVEL2,"--> read_dosenconfig anzahl gefunden. {}". format (dosen))
    else:
        myprint(DEBUG_LEVEL0,"--> read_dosenconfig nehme defaultwert 4 dosen")
        dosen = 4        

    return (dosen)


# write file dosenconfig--------------- 
# er wird der config-File dosen.ini jedesmal neu geschrieben, er enthält nur eine Sektion mit zwei tuples 
# neu im Januar 2019
def write_dosenconfig (filename, myprint, wert, debug):
    dosen= 99                   # default wert bei not found
    found = False
    myprint (DEBUG_LEVEL2,"--> write_dosenconfig {} called".format (wert))
#  erst alle Werte im config löschen, damit nur die neuen Tuple geschrieben werden.
    
    for section in parser.sections():
        parser.remove_section(section)
   
    try:                                # prüfen, ob der File schon existiert
        fp = open(filename)
        ret=parser.readfp (fp) 
        if parser.has_section("anzdosen"):     # sektion vorhanden ?

            for name, value in parser.items("anzdosen"):   # returns a list of tuples containing the name-value pairs.
                if debug > DEBUG_LEVEL2:
                    print ("Name: {}  Value: {} ".format(name, value))
                if name == "anzahl":
                    dosen= int(value)               # entnehme die anzahl
                    found = True     
            fp.close()                      # close file           
        else:
            myprint (DEBUG_LEVEL0,"ConfigRead Abschnitt {} fehlt in Configfile {}".format("anzdosen","swdosen.ini"))  
        
        myprint (DEBUG_LEVEL2,"Dosen anzahl gefunden: {}".format(dosen))
    except FileNotFoundError:
        myprint (DEBUG_LEVEL2,"File swdosen.ini nicht gefunden, wird neu erstellt")

    myprint (DEBUG_LEVEL3,"--> ConfigRead write_value found: {} gefunden. {} neu: {}". format (found, dosen, str(wert)))

    if (dosen != wert):
    
    # zuerst alle Werte im config löschen, damit nur die neuen Tuple geschrieben werden.
        myprint (DEBUG_LEVEL2,"--> ConfigRead write_value nun schreiben")       
        for section in parser.sections():
            parser.remove_section(section)

        cfgfile = open(filename,'w')

        parser.add_section('anzdosen')
        parser.set('anzdosen', 'anzahl', str(wert)) 
        parser.set('anzdosen', 'written', str(datetime.now()))

# writing our configuration file to 'swdosen.ini'
        parser.write(cfgfile)
        cfgfile.close()
        myprint (DEBUG_LEVEL0,"--> ConfigRead write file swdosen.ini geschrieben, Anzahl: {}".format(str(wert))) 
    else:
        myprint (DEBUG_LEVEL1,"--> ConfigRead write anzahl dosen identisch, nichts schreiben")


# --------------------------

            
# *************************************************
# Program starts here
# *************************************************

# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("configread_dosen.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
#**************************************************************
#  That is the end
#***************************************************************
#