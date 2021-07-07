#!/usr/bin/python
# coding: utf-8
# ***********************************************************
# 	Class ActionList 
#   
#   enkapsuliert die Behandlung der XML Steuerfiles
#   Read, Parse, Ausgabe der Aktionsliste
#
#   diese Class erbt von der MyPrint Class
#   
#   folgende public methods stehen zur Verfügung:
#       get_ActionList()
#       print_actions()
#       show_anzdevices()

#       set_debug()
#
#
#   folgende privat methods gibt es:
#  
#       __parse_file()
#       __datechange()
#
#   Verbessert Januar 2015, P.K. Boxler     , angepasst für Switcher2 im Juli 2018
#
# ***** Imports *********************************************
import sys, getopt, os
import xml.dom.minidom
from datetime import date
import datetime
import math
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sys import version_info

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

#-------------------------------------------------
# Class Parser, erbt vom Class MyPrint
#--------------------------------------------------
class ActionList(MyPrint):
    ' klasse ActionList '
    
#    Definition der Class Variables
    parserzahler=0           # Class variable Anzahl Parser instanzen

    monate={"Januar":"Jan","Februar":"Feb","März":"Mar","April":"Apr","Mai":"May","Juni":"Jun","Juli":"Jul", "August":"Aug","September":"Sep","Oktober":"Oct","November":"Nov","Dezember":"Dec"} 
        
# Konstruktor der Class ------------------------        
    def __init__(self,debug_in, path_in):   # Init Methode der Dose, setzt Instanz Variablen
#
#   Defintion der Instanz Variablen ----------
        self.Weekdays={0: "Sonntag", 1:"Montag", 2: "Dienstag",3: "Mittwoch",4: "Donnerstag",5: "Freitag", 6: "Samstag"}
#        self.Weekdays={0: "Set 1", 1:"Set 2", 2: "Set 3",3: "Set 4"}
        self.onoff={1:'ON', 0:'OFF'}
        self.maxlen=90
        self.maxdevice=8                  # Platz für maximal 8 Devices 
        self.maxday=7
#       self.season=0
        self.debug=debug_in
        self.file_id =""
        self.path=path_in       # pfad wo switcher2 läuft
        self.myprint (DEBUG_LEVEL2,  "--> ActionList init called")
        self.dates=[[] for i in range (2)]
        self.heute=0
        self.anz_devices = 0


#-----------------------------------------

#-------------------------------------------
# __repr__ function class ActionList
# 
    def __repr__ (self):

        rep = "ActionList ( )"
        return (rep)

#------- Public Method to set debug -------------------
    def set_debug(self,debug_in):
        self.myprint (DEBUG_LEVEL2, "--> ActionList set_debug called mit {}".format(debug_in))
    
        self.debug=debug_in

#------- Public Method to set return anzahl devices in xml File -------------------
    def show_anzdevices(self):
        self.myprint (DEBUG_LEVEL2, "--> show_anzdevices called")
    
        return (self.anz_devices)



# ***** Public Method print alle Aktionen in Liste 1, 2 und 3 *************
    def print_actions(self, li_tage,li_device, li_zimmer):
    
        print ( "\n-----------------------------------------------------------------------")
        print (  "---- Liste aller Aktionen in Steuerfile:  %s" % (self.file_id) )
        print (  "-----------------------------------------------------------------------")
   
        switch = " "
    
    #
    #  Liste 1 *********************************************
    #
        print( "Liste 1:  Aktionen pro Wochentag ---------------\n")
        for wochentag , tag in enumerate(li_tage):       # loop über alle Tage 
  
            l = len(tag)                # hat Tag überhaupt Aktionen ?
            if l != 0:                              # ja, hat er
                print (  "Tag: {tag} - Anzahl Aktionen: {aktion}".format (tag=self.Weekdays[wochentag], aktion=l) )
                for aktion in tag:      # loop über alle Aktionen eines Tages
                    switch = "On"
	# hole ein/aus für action j am tag i			
                    if aktion[5] == 0:
                        switch = "Off"
               #     print ( "Zeit: %s Device: %s/%15s Switch %s" % (aktion[0],aktion[1], li_zimmer[aktion[1]-1], switch))
                    print ( "Zeit: {zeit} Device: {device}/{wtag} {aktion}".format (zeit=aktion[0],device=aktion[4], wtag=li_zimmer[aktion[4]-1], aktion=switch))
        print (  "Ende Liste Aktionen pro Wochentag ----------------------\n")
    
    #
    #  Liste 2 ***********************************************
    #       Liste über alle Tage, pro Tag alle Dosen und pro Dose alle Aktionen

        print ( "Liste 2: Aktionen pro Device ----------------------")
        
     
   #     print (tag_device_liste)
   
        for wochentag, tag in enumerate (li_device):                    # loop über alle Tage
            if wochentag >6: break
            print (  "\n---- %s  ----------------" % self.Weekdays [wochentag] )
            for devicenummer, device in enumerate(tag):                 # loop ueber alle dosen des tages
                anzact = len(device)                                    # number of actions for this dose on this day
       
                if anzact == 0:
                    continue     #  keine Aktionen, also skip 
                print ("---- Device %d, Anzahl Actions %d " % ((devicenummer),anzact))

                if anzact % 2:
                    print ("Error, Device %s hat ungerade Anzahl Actions -------"   %  anzact  )     
#                 
                for k in range(0,anzact,2):                             # loop über alle Aktionen einer Dose
                    print ("Zeit: %s, Action: %s" % (device[k][0],self.onoff[device[k][5]])  )
                    print ("Zeit: %s, Action: %s" % (device[k+1][0],self.onoff[device[k+1][5]])  )
    

        pass
# -----------------------------
## Ende einer Dose
#-----------------------------
        pass
# -----------------------------
# Ende aller Dosen
#-----------------------------

        pass

# -----------------------------
# Ende aller Tage
#-----------------------------
        print (  "Ende Liste Aktionen pro Device ------------------------\n")
    #    print ('\r' )
        print ( "Liste 3: Gefundene Zimmer -----------------------------\n")
        for item in li_zimmer:
            print ("Zimmer: {}".format(item))    
 
        print (  "-----------------------------------------------------------------------")
        print (  "---- ENDE Liste aller Aktionen in Steuerfile:  %s" % (self.file_id) )
        print (  "-----------------------------------------------------------------------")


# *************************************************

    def getText(self,nodelist):
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
        return ''.join(rc)


# ***** Public Method readfile (xml-file) and parse ***************
#       lesen des passenden XML Files und versorgen der Daten in
#       den listen li_tage und li_devicen 
#--------------------------------------------------------------------------
    def __parse_file (self, filename,li_tage,li_device,li_zimmer):
        ret = 0
 
        self.myprint (DEBUG_LEVEL2,  "ActionList Start Parsing Inputfile: %s " % (filename))
        try:
            DOMTree = xml.dom.minidom.parse(filename)
            aktionen = DOMTree.documentElement
        except xml.parsers.expat.ExpatError as e:
            self.myprint (DEBUG_LEVEL0,  "ActionList: XML File ist nicht ok, not well formed, muss aufhoeren")
            self.myprint (DEBUG_LEVEL0,  "Parser meldet dies:")        
            self.myprint (DEBUG_LEVEL0,  "{}".format(e))   
            ret=9
            return(ret)
#  ok, xml file scheint io

        try:
            self.file_id = aktionen.getElementsByTagName("file_id")[0].firstChild.data
 
        except:
            self.myprint (DEBUG_LEVEL0,  "Element file_id  nicht gefunden im File: {}" .format(filename))
            ret=9
            return(ret)
    
        action=list()
        actionListperDay=list()
 
        d=0
        s=0

        if ret > 0: 
            return(ret)             # error return

     # we proceed......


#   Erklärung des Elements list_tage: das ist eine Liste von Listen
#   -----------------------------------------------------------
#   Nämlich:

#   Eine Liste von 7 Elementen Weekday (eines für jeden Wochentag 0-7) 
#   Jedes Element Weekday ist eine Liste von Schaltaktionen (actions) für den Wochentag
#   Jede Schaltaktion (action) ist ebenfalls einen Liste (mit 6 Elemente))
#
#----------------------------------------------------------
    #   Eine Aktion sieht so aus:
    #   Element action = ("HH.MM", Zeit in Min, Dauer in Min, "HH.MM", Dose, ON/OFF)
    #   elemente:
    #   0: erstes "HH.MM" element ist ev. korrigierte Schaltezeit
    #   1: selbe Schaltzeit aber in Minuten des Tages
    #   2: Dauer eingeschaltet in Minuten
    #   3: zweites "HH.MM" element ist originale Schaltzeit (vor adjust)
    #   4: Dosennummer
    #   5: 1 = einschalten / 0 = ausschalten
    #-------------------------------------------------------------
#
#           
#   Erklärung des Elements liste_dose : das ist eine Liste von Listen von Listen
#   ----------------------------------------------------------------------
#   Nämlich:
#
#   Eine Liste von n Dosen-Elementen (eines für jede Dose 0-4, maximal 5) 
#   Jedes Dosen-Element besteht Wochentages-Elementen (0-7)
#   Jedes Wochentag-Element besteht aus einer Liste von Schaltaktionen
#   Jede Schaltaktion (action2) ist ebenfalls einen Liste (Zeit, On/Off)
#
    
        devices = aktionen.getElementsByTagName("device")
        
        # add Device-list to all weekdays
        for tage in li_device:
            for y in range (len(devices)+1):
                tage.append([])  

    #    for i in range(self.maxday):
    #        li_device.append([])     # append tageslist 
    #        li_tage.append([])     # append tageslist 
    #        for y in range (len(devices)+1):
    #            li_device[i].append([])  
            
       # print ("Anzahl Tage: {} ". format(len(li_tage)))

#
        self.anz_devices = len(devices)
        self.myprint (DEBUG_LEVEL1,  "Anzahl Devices:{}".format(self.anz_devices))
#   Main Loop for parsing -----------------
        for device in devices:                              # loop über alle Dosen im File 
            
            if device.hasAttribute("name"):
                zimmer = device.getAttribute("name")
        
#           d+=1                    # dose 0 skippen 
            devicenummer = int(device.getElementsByTagName("device_nr")[0].firstChild.data)
            li_zimmer.append(zimmer)

            self.myprint (DEBUG_LEVEL3,  "Process Devicenummer: {}  Zimmer: {} -----------------".format(devicenummer,zimmer))
                
# get days for a Device
            days = device.getElementsByTagName("tag")	
            self.myprint (DEBUG_LEVEL3,  "Anzahl Tage für device: {} / {} ".format( len(days), device))

  #      print (li_tage)

            for day in days:                            # loop über alle Tage einer Dose
# get weekday number for a day	

                if day.hasAttribute("nummer"):
                    wochentag = int(day.getAttribute("nummer"))
                
                self.myprint (DEBUG_LEVEL3, "--------------------------------------")
                self.myprint (DEBUG_LEVEL3,  "Processing  weekday: %s" % wochentag)
# get off/on sequences for a weekday
                sequenzen = day.getElementsByTagName("sequence")	
                self.myprint (DEBUG_LEVEL3,  "Anzahl Sequenzen: {}".format(len(sequenzen)))

                # create a list of action elements ---------------------------------------

                for sequenz in sequenzen:       # a sequence contains ON time and OFF time 
                    s+=1
                    start = str(sequenz.getElementsByTagName("ON")[0].firstChild.data)      # extract ON time (start) is "hh.mm"
                    stop = str(sequenz.getElementsByTagName("OFF")[0].firstChild.data)      # extract OFF time (stop) is "hh.mm"
                
                # calculate dauer between ON and OFF (added 2021)
                    hhmm_s = start.split(".")
                    hhmm_e = stop.split(".")
                    start_time = (60 * int(hhmm_s[0])) + int(hhmm_s[1])       # minuten des Tages
                    stop_time    =   (60 * int(hhmm_e[0])) + int(hhmm_e[1])       # minuten des Tages
                    dauer = stop_time-start_time

                    self.myprint (DEBUG_LEVEL3, "Processing Device %s  Wochentag %s " % (devicenummer,wochentag)	)	
                    self.myprint (DEBUG_LEVEL3, "Device:{} Wochentag:{} ON/OFF:{}/{} dauer:{}".format( devicenummer,wochentag, start,stop ,dauer))
                   	
                
                # create an action element from a sequence in the xml file
                #   für ON Zeit  <-----
                #   eine action element hat die Form: ["hh.mm" , int, int, int,int]              # action ist list aus 5 Elementen
                #   konkret: ["12.30", schaltzeit in Min, dauer in min, dose-nr, 1]              # letztes element 1= on, 0= off   
                    
                 #   action = [start, start_time, dauer, devicenummer, 1]    # this an ON action element
                    action = [start, start_time , dauer, start, devicenummer, 1]    # this an ON action element
    
                # now add this action element to both lists
                    li_tage[wochentag].append(action)                       # append this action zum Wochentag
                    li_device[wochentag][devicenummer].append(action)       # append this actions zum Wochentag und Dosennummer            
                    
                    self.myprint (DEBUG_LEVEL3, "Action-Element ON  fuer Device: %s  Wochentag: %s action: %s" % (devicenummer,wochentag,action) )


                # ditto für OFF Zeit  <-----     
                    action = [stop, stop_time, dauer, stop, devicenummer, 0]      # this is an OFF action element

                # now add this action element to both lists
                    li_tage[wochentag].append(action)                       # append this action zum Wochentag
                    li_device[wochentag][devicenummer].append(action)       # append this actions zum Wochentag und Dosennummer

                    self.myprint (DEBUG_LEVEL3, "Action-Element OFF fuer Device: %s  Wochentag: %s action: %s" % (devicenummer,wochentag,action) )
     
# done with wochentag -------------------------------------
                self.myprint (DEBUG_LEVEL3,  "Done with Device: {} Tag: {}".format(devicenummer,wochentag))
            
           
# done with a day ----------------------------------------
            self.myprint (DEBUG_LEVEL3, "Done with Days for Device {}".format(devicenummer))

# done with devices ----------------------------------------
        self.myprint (DEBUG_LEVEL2,  "Done with Devices   ")

        for i in range(len(li_tage)):       # ueber alle tage
#        x=li_tage[i].pop(0)
#        x=li_tage[0][i].pop(0)             # dose 0 war zuviel, wegen Art der nummerierung der Dosen !!
            li_tage[i].sort()
    						
        self.myprint (DEBUG_LEVEL2, "\nAnzahl Devices gefunden: {}".format(len(devices)))
        self.myprint (DEBUG_LEVEL2, "Anzahl Sequenzen gefunden: {}".format(s))
#        self.myprint (DEBUG_LEVEL2, "ActionList Done Parsing Inputfile")
        self.maxdevice = len(devices)               # uebernehme dies für printout anzahl dosen
        return(ret)
# *************************************************

#-------------------------------------------
# Public Method: Einlesen und Parsen der Steuerfiles
#  Parameter li_tage und li_device  sind zwei Listen, die vom Caller übergeben werden
#   sie werden hier abgefüllt mit den Daten aus dem XML File 
#   values ist liste der Daten aus dem Config-File, dort finden wir XML-Filename-Prefix und den namen der saison
#------------------------------------------
    def get_actionList(self,li_tage,li_device,li_zimmer,values):
        ret = 0
#   Etablieren des Pfads der Steuerfiles, sind im Subdir xml des switcher dirs
        self.path = self.path + "/xml"
        self.myprint (DEBUG_LEVEL1,  "ActionList Pfad fuer Steuerfile: {}".format(self.path))
# Einlesen und Parsen der Steuer-Files für alle ActionList.saison_list             alles neu juni2018
#-------------------------------------------------------   
#    zuerst namen der Files aus dem Congi-File holen - die Werte stehen schon in values
       
    
                                                                               
#  Lesen des xml Steuer-Files , Filename erstellen--------------    
        xmlfile1 = self.path + "/" + values["ctrl_file"]  + ".xml"
 
# check ob file existiert
        if os.path.exists(xmlfile1):
            self.myprint (DEBUG_LEVEL1, "ActionList XML Steuerfile gefunden: %s" % xmlfile1)	# file found
        else:
            self.myprint (DEBUG_LEVEL0, "ActionList XML Steuerfile %s nicht gefunden" % xmlfile1)	# file not found      
            sys.exit(2)
 
        self.myprint (DEBUG_LEVEL3, "filename: %s " % (xmlfile1))
#-----------------------
#       File found, nun parsen und versorgen 
        ret = self.__parse_file(xmlfile1,li_tage,li_device,li_zimmer)			# parse Input Datei (XML) 	and fill lists with data
#-----------------------
        if ret > 0:
            self.myprint (DEBUG_LEVEL0, "ActionList Fehler bei Parsen von File: {}".format(xmlfile1))
   


        self.myprint (DEBUG_LEVEL2,  "ActionList Parsing done, retcode: {}".format(ret))	
#   
        return (ret, self.file_id)                 # we are done ---------------
# 

#      bei grossem debug die Liste aller Aktionen ausgeben
#        if self.debug > DEBUG_LEVEL2:
#            for y in range(len(li_tage[0])):
#                print ("Tag: {}".format(y))
#                for i in range(len(li_tage[0][y])):
#                    print (li_tage[0][y][i])
#                    
       
#        return(ret,"")
#---------------------------------------------------------
#


#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swactionlist.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    

