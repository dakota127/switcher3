#!/usr/bin/python3
# coding: utf-8

# -----------------------------------------
# Script zum Testen der XML Steuerfiles Switcher2
#
# Aufruf (Beispiel, wenn Files im Dir xml liegen):
#
#   python3 python3 swtestxml.py -f xml/swhaus1-test3-zwischen.xml
#

# https://www.tutorialspoint.com/python3/python_xml_processing.htm
#-----------------------------------------------------------------
#from xml.dom.minidom import parse
import xml.dom.minidom
import sys, os
import argparse

maxdosen = 7
tageliste = [ [] for z in range (maxdosen)]
list_dosenname = []
listdosennummern = []
error = []
filename = ""
debug = 0
aktionen=0
totaltag=[[],[],[],[],[],[]]

monate=["Januar","Jan","Februar","Feb","März","Mar","April","Apr","Mai","May","Juni","Jun","Juli","Jul", "August","Aug","September","Sep","Oktober","Oct","November","Nov","Dezember","Dec"] 

fehler =[ [] for z in range (14)] 
fehler [0] = ""
fehler [1] = "Kein Attribute Saison im Root Element gefunden"
fehler [2] = "Tagesnummer bei einer Dose fehlerhaft"
fehler [3] = "ON/OFF Elemente sind fehlerhaft"
fehler [4] = "Weniger als 4 Dosen definiert"
fehler [5] = "Dosennnummern sind irgendwo falsch"
fehler [6] = "Sommer/Wintersaison muss Element von/bis Datum haben"
fehler [7] = "Zwischensaison darf kein Element von/bis Datum haben"
fehler [8] = "Kein Element file_id vorhanden"
fehler [9] = "Dosennnumern sind nicht aufsteigend"
fehler [10] = "Element <from_date> oder <to_date> (Saison) ist fehlerhaft"
fehler [11] = "Monat in <from_date> oder <to_date> (Saison) ist fehlerhaft"
fehler [12] = "Eine Dose hat nicht genau 7 Tage definiert"
#----------------------------------------------------------
# get and parse commandline args
def argu():
    global filename
    global debug

    parser = argparse.ArgumentParser()

    parser.add_argument("-d", help="Debug", action='store_true')
    parser.add_argument("-f", help="XML Filename", default="", type=str)


    args = parser.parse_args()
#    print (args.d, args.s, args.dein, args.daus, args.dnor, args.dexc, args.dinc)          # initial debug
#    if args.s:
#        print ("s war hier")
    if args.d:
        debug=1
    if args.f : filename = args.f    # filename
     
    return(args)
  
# --------------------------------
def check_onoff(element):
    global error
    
    pass
    err=0
    text =""
    if len(element) != 5:
        error.append(3)
        err = 9
        text= "ON/OFF Element ist nicht Laenge 5: {}".format(element)
        return [err,text]

    try:
        hour,min = element.split(".")
    except:
        err = 9
        text= "ON/OFF Element ist nicht Format hh.mm: {}".format(element)
        return [err,text]

    hint =0
    mint =0
    if hour.isnumeric():
        hint = int(hour)
    if min.isnumeric():
        mint = int(min)
    
    if  hint > 23:
        err = 9
        text= "ON/OFF Element hat ungueltige Stunde {}".format(element)
        return [err,text]
        
    if  mint > 59:
        err = 9
        text= "ON/OFF Element hat ungueltige Minute {}".format(element)
        return [err,text]   
    
    return [0,""]
    
    
#--------------------------------
def check_vonbis(element):

    try:
        a,b = element.split(".")
    except:
        error.append(10)
        print ("Element von/bis nicht in Ordnung: {}".format (element))
        return
    found = False
    for mon in monate:

        if b == mon:
            found = True
    if not found:
        error.append(11)
        print ("Element von/bis der Monat ist falsch: {}".format (element))
        return
    if a.isnumeric():
        tagvon = int(a)
        pass
    else:
        print ("Element von/bis nicht in Ordnung: {}".format (element))
        error.append(10)    
        print (a)   
    
    if  tagvon == 0 or tagvon > 31:
        print ("Element von/bis hat falschen Tag des Monats: {}".format (element))
        error.append(10)          

#  ---- Element von bis behandeln--------------  
def find_vonbis(saison):
    found=0
    try:    
        von = aktionen.getElementsByTagName('from_date')[0]
        vond = von.childNodes[0].data
        if debug:
            print ("Datum von: {}".format(vond))
        check_vonbis(vond)
        found += 1
    except:
   
        if debug:
            print ("Kein von datum gefunden")
  
    try:    
        bis = aktionen.getElementsByTagName('to_date')[0]
        bisd = bis.childNodes[0].data
        if debug:
            print ("Datum bis: {}".format(bisd))
        check_vonbis(bisd)
        found += 1
    except:
      
        if debug:
            print ("Kein bis datum gefunden")

    
    return 
  
#-------------------------------------------
def runit(filename):
    global error
    dosencounter = 0
    anzseqtot = 0
    text = ""
    global tageliste
    global aktionen
    # Open XML document using minidom parser
    
    # Prüfungen durchführen
    print ("\n ----- Pruefbericht ----------------------\n")
    print ("Begin der Pruefung der Datei: {}".format(filename))
    
    try:
        DOMTree = xml.dom.minidom.parse(filename)
        aktionen = DOMTree.documentElement
    except xml.parsers.expat.ExpatError as e:
        print("XML File ist nicht ok, not well formed, muss aufhoeren")
        print("Parser meldet dies:")        
        print (e)
        sys.exit(2)
        
    

    try:
        fileid  = aktionen.getElementsByTagName("file_id")[0].firstChild.data  
        if debug:
            print("File-ID: {}".format(fileid))       
    except:
        error.append(8)
        return(error)
        
        
    # 
    try:
        dosen = aktionen.getElementsByTagName("device")
        anzdosen = len (dosen)
    except:
        print("Parsing Problem mit den Dosen, kann nicht weiter machen")
        sys.exit(2)
                
    # Dosen verarbeiten
    if debug:
        print("Start mit Dosen")
        print (listdosennummern)
    for dose in dosen:
        if debug:
            print ("*****Dose {} *****".format(dosencounter))
        if dose.hasAttribute("name"):
            namedose = dose.getAttribute("name")
            if debug:
                print ("Name: %s" % namedose)
            list_dosenname.append(dose.getAttribute("name"))         # Liste der Dosennamen

        nummer = dose.getElementsByTagName('device_nr')[0]
        dosennummer = int(nummer.childNodes[0].data)
        listdosennummern.append(dosennummer)
        if debug:
            print ("Dosencounter: {} und Dosennummer: {}".format(dosencounter,dosennummer))

        if debug:
            print ("Behandle Tage fuer die Dose")
        tage = dose.getElementsByTagName("tag")
        for tag in tage:
            if tag.hasAttribute("nummer"):
                tagin = int(tag.getAttribute("nummer"))
                if debug:
                    print ("Tagnummer: %s" % tagin)
                tageliste[dosennummer].append(tagin)
            if debug: 
                print ("Behandle Sequenzen fuer den Tag")
            sequ = tag.getElementsByTagName("sequence")	
            anzseq = len(sequ)
            anzseqtot += anzseq
            for seq in sequ:
                on = seq.getElementsByTagName("ON")[0].firstChild.data
                erro = check_onoff(on)
                if erro[0] > 0:
                    print ("Dose: {}  {} ".format(dosencounter,erro[1]))
                    
                off =  seq.getElementsByTagName("OFF")[0].firstChild.data                    
                erro = check_onoff(off)
                if erro[0] > 0:
                    print ("Dose: {}  {} ".format(dosencounter,erro[1]))

          
            if debug:
                print ("Anzahl Sequenzen: {}".format(anzseq))
        dosencounter += 1


    
# Test0: Anzahl der gefundenen Dosen


    if len(listdosennummern) != 5:
        print ("Statt 5 Dosen sind nur {} Dosen definiert".format(anzdosen))
        error.append(4)
    total = 0
    total2 = 0
    ctr = 0

# test 1 : sind Dosennummern aufsteigend 
    err = 0
    for i, dose in enumerate(listdosennummern):
        if i+1 != dose:
            print ("Gefundene Dose {} hat falsche Dosennummer: {}".format(i+1,dose))
            err = 1

    if err > 0:
        error.append(5)
        print ("Die Dosennummern sind falsch, hier Liste der Dosennummern:")
        print ("Liste: {}\n".format(listdosennummern))
    err = 0
    
 # Test 2:  Tage prüfen    

   # for i in range (maxdosen - dosencounter-1):
   #     print(i, dosencounter)
   #     pass
   #     tageliste.pop(0)    
 

    print ("\nPrüfe Tage pro Dose")

    for i in range (dosencounter): 
        i=i+1
        if debug: 
            print ("Tageliste: {}".format(tageliste[i]))

        anzt = len(tageliste[i])
        print ("Anzahl Tage in Dose: {}/{}".format(i,anzt))
        if anzt > 7 or anzt < 7 :
            print ("Gefundene Dose {} hat nicht genau 7 Tage: {}".format(i,anzt))
            error.append(12)
        for z, tag in enumerate(tageliste[i]):  
            if z != tag:
                print ("Gefundene Dose {} hat falsche Tagesnummer: {}".format(z,tag))
                err = 1

    if err > 0:
        print ("Bei einer Dosen sind Tagesnummern falsch, hier Liste der Tagesnummern:")
        print ("Liste: {}\n".format(tageliste))
        error.append(2)
    
    err = 0 
    

    for i, dose in enumerate(tageliste):
        for tag in dose:
            total += tag        # total der tage in der Dose, muss 16 sein
        if total != 21: 
            pass
        else:
            ctr += 1
        total2 += total
        total=0

    if debug:
        print ("total Tageszaehler: {}".format(total))
    

    
    print ("\nGefunden in der Datei:")   
    print ("Total Dosen: {}".format(anzdosen)) 
    print ("Total Sequenzen: {}".format(anzseqtot))
    print ("Namen der Dosen: {} ".format(list_dosenname))
    return (error)
#
#    
# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    options=argu()                          # get commandline args

 #   Etablieren des Pfads 
    pfad=os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft

    if len(filename) == 0:
        print ("Error: kein XML File angegeben")
        sys.exit(2)
    if not os.path.exists(filename):
        print ("File: {} nicht vorhanden".format(filename))    
        sys.exit(2)
#
#    ok File scheint vorhanden
    err = runit(filename)

    if len(err) >0:
        print ("\nDatei: {} \nEtwas ist nicht korrekt in diesem File\nZusammenfassung:".format(filename))
        print (error)
        for item in error:
            print (fehler[item])
    else:
        print ("\nDatei: {} ist in Ordnung\n".format(filename))

    print ("\n ----- Ende Pruefbericht ----------------------\n")
 
