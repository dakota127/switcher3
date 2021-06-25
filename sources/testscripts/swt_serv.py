#!/usr/bin/env python
# coding: utf-8
#
# --------------------------------------------------------------
#   Test Programm to Test Messages to and from swserver3.py
# 
#   There is a companion Programm to test Messages to and from swswitcher3.py

#   Author: Peter K. Boxler, March 2021, 
#------------------------------------------------------------


import sys, getopt, os
from time import sleep
import json
import sys
import argparse
import paho.mqtt.client as mqtt
import time
from sys import version_info
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.myconfig import ConfigRead
from sub.mymqtt import MQTT_Conn              # Class MQTT_Conn handles MQTT stuff
from sub.swc_connector import SwConnector           # Class SwConnector


REQUEST_RETRIES=3
REQUEST_TIMEOUT=3500

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

MQTT_TOPIC_PUB =   "test"           # test
MQTT_TOPIC_SUB =   "test2"           # test2
MQTT_TOPIC_CMD =   "commands"
MQTT_TOPIC_RESP =   "response"           # PUB sending to flask server


mqtt_broker_ip_cmdline = ""     # ipc adr from commandline

lastcommand=""
web=0
client=0
poll=0
context=0
debug=0
# instances of classes
myprint     = None
swconnector = None
onoff = 1
home_nothome = 1

reboot_verlangt = 0
valid_commands =  [                 # tuple of valid commands
        "",
        "help",
        "stop" ,                  #  terminate switcher
        "alist",
        "sdeb" ,                   # switcher stop debug output
        "mdeb",                    # switcher start debug output
        "stat",                    # switcher gebe status zurück
        "stad" ,                     # kurzen status
        "x",                    # terminate the client (not switcher)
        "spez",
        "d1",
        "d2",
        "d3",
        "d4",
        "d5",
        "d1auto",
        "d2auto",
        "d3auto",
        "d4auto",
        "d5auto",        
        "aein",
        "aaus",
        "home",
        "swi",
        "mmit",
        "mnie",
        "wett",
        "rebo",             # sende reboot verlangt an den switcher
        "reboc"             # dieser client mach reboot pi
        
        ]                    # switcher soll antwort verspätet senden

anz_commands=0
#------------------------------    

sequence = 0

i=0
anzerr=0
anztry=3
message=" "
stop=0
slog=0
ret=0
debug=0
ipc=0
endpoint =""
#
config=0
mypri=0
progname = "swt_serv"
logfile_name = "switcher3.log"
configfile_name = "swconfig.ini"
printstring = "swt_serv: "

EXSTAT      = ["Aus","Ein"]
HOMESTATE={0:'Niemand daheim', 1:'Jemand zuhause'} 





#----------------------------------------------------------
# get and parse commandline args
def argu():
    global debug
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", help="kleiner debug", action='store_true')
    parser.add_argument("-D", help="grosser debug", action='store_true')
    parser.add_argument("-A", help="ganz grosser debug", action='store_true')
    parser.add_argument("-s",       help="Nur Statusausgabe", action='store_true')
    parser.add_argument("-dein",    help="Dose manuell ein", default=0, type=int)
    parser.add_argument("-daus",    help="Dose manuell aus", default=0, type=int)
    parser.add_argument("-dnor",    help="Dose normal",default=0, type=int)


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
def setup():
    global anz_commands
    global options, myprint, swconnector
    global config, mypri
    global logfile_name, configfile_name
  
    print ("Testprogramm to test swserver3.py\n")
    options=argu()                          # get commandline args

    path = os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft

# create Instance of MyPrint Class 
    myprint = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  path + "/" + logfile_name ) 
  

    myprint.myprint (DEBUG_LEVEL0, "Name logfile: {} ".format( path + "/" + logfile_name) )
    myprint.myprint (DEBUG_LEVEL0, "Name configfile: {} ".format( path + "/" + configfile_name) ) 

 

    #------------------------------------
    #  create Instance of SwConnector Class  
    swconnector = SwConnector ( debug = debug, 
                                path = path,
                                configfile = configfile_name,
                                endpoint = 1,
                                mqtt_client = None,
                                callback = notifyServer)
    time.sleep(1)    
              

    anz_commands=len (valid_commands)

    # check mqtt status
    mqtt_connect, mqtt_error = swconnector.mqtt_status()
    if mqtt_connect == False:
        print ("swt_serv.py: Keine mqtt Connection möglich")
        return (mqtt_error)

    else:
        # init for receiving of sync messages (only needed on client side)
        swconnector.request_response_init (MQTT_TOPIC_RESP)
        return (0)

# fertig setup()

#-------------------------------------------
# assemble status list for dose
def stat_list2():
    dos_list =[]
    dos_list.append (1)
    dos_list.append (1)                    # externer status
    dos_list.append ("Ein")            # externer status
    dos_list.append (1)
    dos_list.append ("Ein")
    dos_list.append (1)
    dos_list.append ("auto")
    dos_list.append ("Typ0")
    dos_list.append ("mqtt")
    dos_list.append ("keller")
    dos_list.append (0)                     # reserve

    return (dos_list)


# handle incoming messages from swserver3 
#---------------------------------------------------------
def notifyServer (art,message_in):
    global  terminate

    myprint.myprint (DEBUG_LEVEL0, " ")
    myprint.myprint (DEBUG_LEVEL1,   progname + "notifyServer called, art:{}, msg:{}".format(art, message))	
    if isinstance(message, str) == True:
        print ("message is string")
   # print (message[0])
   # print (message[1])
#   switcher meldet, was er gemacht hat 
#   message[2] enthält auto oder manuell, je nach dem, warum das device geschaltet wurde
#
    if isinstance(message_in, list) == True:
        if isinstance(message_in[0], str) == True:
            print ("-----> Meldungsstrukur ist OK")
        else :    
            print ("-----> Meldungsstrukur ist FEHLERHAFT")
 
    print ("\t message_in:{}".format(message_in))
   

    myprint.myprint (DEBUG_LEVEL0, "\n -----------> press enter to continue  <--------------------")

#- do publish  to switcher3
#-------------------------------------------------------------       
def messageOut (meldung):
    myprint.myprint (DEBUG_LEVEL0, progname + ": messageOut: {} ".format(meldung))
    payl=json.dumps(meldung)          # umwandeln in JSON Object (also ein String)    
   
    swconnector.transmit (payl) 
   
 #  mqtt_error = mqttc.publish_msg (MQTT_TOPIC_PUBSWIT, payl)
 #   if (mqtt_error > 0):
 #       myprint.myprint (DEBUG_LEVEL0,  "publish returns: {} ".format(mqtt_error))



#  NOT USED
#----------------------------------------------------------
def printReply(meldung):
    spos=0
    epos=0
    
    if meldung.find("stat") == -1 and meldung.find("stad") == -1 and meldung.find("wett") == -1: 
        print ("Antwort vom switcher3: %s" % meldung)
        return       #  ss ist nicht stat oder stad oder wett

    # es ist antwort auf statusrequest oder wetter
    meldung = meldung[4:]         # entferne meldungs id 4 char

    try:
        meld=json.loads(meldung)   # JSON Object wird in Python List of List gewandelt
    except:
        print ("Status string nicht gut...")
        return

    # antwort besteht aus einer Liste mit Einträgen
    # index[0] sind die Daten an den Webserver
    # restliche einträge sind die DAten
    
    print ("Info fuer den Webserver: -------- Anz Items: {}".format(len(meld[0])))  
    for i in range(len(meld[0])):
        print ("{:18}:  {:<18}".format (meld[0][i][0]  ,meld[0][i][1]))
    
    meld.pop(0)             # liste mit indo an den webserver wegpoppen
    
    
    print ("Und nun die Daten: -------------- Anz Items: {}".format(len(meld)))     

#  wetterdaten ist liste laenge 2, alle anderen haben mehr items
#  not very well done..... but it works
    if len(meld) == 2 :         # sind wetterdaten
        for item1 in meld :   
  #          print ("len item1: {}".format(len(item1))) 
            for item2 in item1 :
                print ("{:18}:  {:<18}".format (item2[0]  ,item2[1]))
    else:       # andere daten haben liste mit mehr als 2 items
        for item1 in meld :    
            print ("{:18}:  {:<18}".format (item1[0]  ,item1[1]))    

    print ("--------------------------------------")
#----------------------------------------------------------


#---------------------------------------------
#
#---------------------------------------
def syncmsg(command):
    myprint.myprint (DEBUG_LEVEL1, progname + ": syncmsg: {} ".format(command))
    
    ret, msg_return = swconnector.transmit_sync ( command, 3000)
   # print("return from transmit")
   # print (ret, msg_return)

    answer_ok = False
    
    if ret == 0:
        answer_ok = True
    elif ret == 9:
        myprint.myprint (DEBUG_LEVEL1,  "msg_sync () returned timeout: {}".format(ret))
    else:
        myprint.myprint (DEBUG_LEVEL1,  "msg_sync () returned other error: {}".format(ret))
            
    if answer_ok:
        myprint.myprint (DEBUG_LEVEL1,  "msg_sync () returned this msg: {}".format(msg_return))
                # or do something appropiate
        time.sleep(1)

    
   # mu = json.loads(msg_return) 
    if answer_ok == False:
        print ("NO ANSWER") 
        return (0,"xxx")

    if (command == "home"):
        
        if isinstance(msg_return, list) == True:
            if isinstance(msg_return[0], list) == True:
                if isinstance(msg_return[1], list) == True:
                    if isinstance(msg_return[1][0], list) == True:
                        if isinstance(msg_return[1][1], list) == True:
                            print ("-----> Meldungsstrukur ist OK")
                            #    error behandlung
                        else:
                            print ("-----> Meldungsstrukur ist FEHLERHAFT")
                            return (9,"qqq")
        for item in msg_return[0]:
            print (item)
        print (msg_return[1][0])
        for item in msg_return[1][1]:
            print (item)

        return (0,"ccc")    

    elif (command == "aliste"):

        if isinstance(msg_return, list) == True:
            if isinstance(msg_return[0], list) == True:
                if isinstance(msg_return[1], list) == True:
                    print ("-----> Meldungsstrukur ist OK (list of 2 lists)") 
                else:
                    print ("-----> Meldungsstrukur ist FEHLERHAFT")
                    return (9,"qqq")  
#    error behandlung    
        for item in msg_return[0]:
            print (item)
        for item in msg_return[1]:
            print (item)    
        return (0,"ccc")    

    else:
       print ("NO ANSWER") 
    

    return (0,"bbb")



#-------------Get Command from Keyboard----------------------------------
# falls letzter command stat war, kann dieser mit enter wiederholt werden.
def get_command() :
    while True:
        stop=0
        slog=0
        global lastcommand

        sys.stdout.write("Bitte einen Command eingeben: ")
        if sys.version_info[0] < 3:
            message = raw_input().strip()
        else:
            message = input()
            
        message = message.strip()
       
        return(message)              
#-----------------------------------------------

#----------------------------------
def runit():
    global debug, reboot_verlangt, lastcommand, onoff,home_nothome
# Loop until command term is given
    while True:
        okcommand = True
        if onoff == 1:
            onoff = 0
        else: onoff = 1
        if home_nothome == 1:
            home_nothome = 0
        else: home_nothome = 1

    # get command from user
        cmd=get_command()       # command in cmd  
        cmd = cmd.strip()

     #   if len(cmd)== 0:
     #       cmd = lastcommand
     #   lastcommand = cmd
        meldung = ""
        if (cmd not in  valid_commands):
            print("wrong command, try again") 
            continue          
                                # zuerst spezielle commands behandeln
        if (len(cmd) == 0): continue

        if cmd.find("x") != -1: break 
        
        elif cmd.find("help") == 0:
            print (valid_commands)
            okcommand = False

        elif cmd.find("reboc") != -1: 
            reboot_verlangt = 1
            break 

        elif cmd.find("mdeb") != -1: debug=1
        elif cmd.find("sdeb") != -1: debug=0

        elif cmd[:1] == 'd':
            nr = int(cmd[1:2])
            if nr > 5 : okcommand = False
            print ("dosencommand:{}".format(nr))
            print (cmd)

            listd = stat_list2()
            listd[0] = nr
            listd[1] = onoff
            listd[2] = EXSTAT[onoff]

            meldung = ["done_dev"  , listd]   # publish ack on topic  

        
        
        elif cmd.find("swi") == 0:
           
            meldung = ["done_home"  , [home_nothome, HOMESTATE[home_nothome]] ]  #   


        elif cmd.find("home") == 0: 
           
            syncmsg ("home")
            okcommand = False
        else:
            pass

        if okcommand == True:
#    send to server und wait for reply    
            retcode = messageOut(meldung)           # try to send request
    #    if retcode[0] == 9:                        # server antwortet nicht
     #       break            
      #  printReply(retcode[1])          #  this the string that came back from server
    
#-----------------------------------
# MAIN, starts here
#------------------------------------
if __name__ == "__main__":

    if version_info[0] < 3:
        print("swt_serv.py läuft nur richtig unter Python 3.x, du verwendest Python {}".format(version_info[0]))
        sys.exit(2)

    ret = setup()
    if ret > 0:
        print ("Beende programm")
        sys.exit(2)                 #xxx

    


    # commandline -s verlangt eine Status-Abfrage, dann exit
    if options.s:
        cmd="stat"
        retcode=sendCommand(cmd)           # try to send request

        if retcode[0] == 0:
            printReply(retcode[1])
        sys.exit(2)
        
    elif options.dein >0 :        # dose schaltn verlangt
        cmd="d" + str(options.dein) + "ein"
        retcode=sendCommand(cmd)           # try to send request
       
        sys.exit(2)

    elif options.daus >0 :        # dose schaltn verlangt
        cmd="d" + str(options.daus) + "aus"
        retcode=sendCommand(cmd)           # try to send request
       
        sys.exit(2)

    elif options.dnor >0 :        # dose schaltn verlangt
        cmd="d" + str(options.dnor) + "nor"
        retcode=sendCommand(debug,cmd)           # try to send request

        sys.exit(2)

#  now run the programm, falls vond er Commandline gestartet        
    runit()                 # get commands from Console and send them....
                            # kommt zurück, wenn term command gegeben oder Verbindung nicht geht.
    del ipc                        
    
    if reboot_verlangt == 1:
        print ("Terminating mit reboot pi")
        sleep(2)
        os.system('sudo shutdown -r now')
    else:
        print ("Client terminating...")
#            
#