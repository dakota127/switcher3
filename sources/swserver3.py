#!/usr/bin/python3
# coding: utf-8
# ***********************************************************
#
# This is program TWO of a suite of two programs for the Switcher3 System
#  
# this programm creates a flask webserver
# Runs with Python3   and NOT tested under Python2 
# 
# This version of the program uses the  MQTT_Conn class tha encapsulates MQTT

# Peter Boxler (last change Juni 2021)
# *********************************************************
#
#
from flask import Flask
from flask import render_template,  request
from flask_socketio import SocketIO
import argparse, os, sys
from sys import argv
import psutil
import time
from datetime import date, datetime
from sub.myprint import MyPrint             # Class MyPrint replace print, debug output
from sub.swc_connector import SwConnector           # Class SwConnector
from sub.swc_dosconf import SWDos_conf
from sub.myconfig import ConfigRead
import json
import subprocess
import threading
import socket


#----------------------------------------------------------
# ---------------------------------------------------------
# Change Version of swserver3 here 
# 
server_version = "3.1"
#---------------------------------------------------------
#--------------------------------------------------------



# Create flask app, SocketIO object, and global pi 'thing' object.
app = Flask(__name__)
socketio = SocketIO(app)
##pi_thing = thing.PiThing()
device_1 = 0
device_2 = 0
home_state_t = ""
home_state_b = 0


debug = 0           # debug flag, wird durch commandline parm verändert


# Define Variables
DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

MQTT_TOPIC_PUBASYN =   "swi/as"           # PUB sending to flask server
MQTT_TOPIC_PUBSYNC =   "swi/sync"           # PUB sending to flask server
MQTT_TOPIC_RESP =   "response"           # PUB sending to flask server

TIMEOUT_SYNC = 3000      # ms time out for sync messages
    

mqtt_broker_ip_cmdline = ""     # ipc adr from commandline
mqtt_connect = False
mqtt_error = 0
# instances of classes
myprint     = None
swconnector = None
swdosconf = None
path = 0
TRUEFALSE=[False,True]
progname = "swserver3 "
logfile_name = "switcher3.log"
configfile_name = "swconfig.ini"
config_section = "switcher"                # look up values in this section
bootmsg_1     = "Reboot Switcher 3, danach bitte warten..."
bootmsg_2   = "Switcher wird neu gebootet, bitte warten"
bootmsg_3   = "Switcher wird Shut Down, bitte warten"
reboot_thread = 0
reboot_verlangt = False
shutdown_verlangt = False
initial_data =[]
host_name   = ""
host_ip     = ""
switcher_version = ""
general_error = 0
swi_pid = 0             # pid process switcher
swser_pid = 0           # pid process swserver


anzahl_dosen_definiert = 0

# ***** Variables *****************************
#   Struktur (Directory) der Daten, die aus dem Configfile swconfig.ini gelesen werden
# s  hier die defaultwerte der 'variablen'
cfglist_swi = {
        "testmode"          : "Nein",          # testmode Ja/Nein
        "wetter"            : "Nein",          # wetter benötigt JA/Nein
        "gpio_blink"        : 5,               # gpio pin blink led
        "reserve"           : 'reservedefault',   #
        "debug"             : 0,               #  debug flag, wie commandline parm -d = 1,-D = 2, -A = 3         
        }

# General error Codes
MQTT_ERROR = 55


#  liste der html files: für Schalten der Dosen, verschieden Anzahl Dosenw
select_dosenanz_htmlfiles = [
            "empty",
            "dosen_anz1.html",
            "dosen_anz2.html",
            "dosen_anz3.html",
            "dosen_anz4.html",
            "dosen_anz5.html",
            ]



# ***** Function Parse commandline arguments ***********************
#----------------------------------------------------------
# get and parse commandline args
def argu():
    global debug, mqtt_broker_ip_cmdline, retry

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", help="small debug", action='store_true')
    parser.add_argument("-D", help="medium debug", action='store_true')
    parser.add_argument("-A", help="details debug", action='store_true')
    parser.add_argument("-r", help="retry indicator", action='store_true')
    parser.add_argument("-i", help="IP Addr", type=str)
    args = parser.parse_args()

    if args.d:
        debug=DEBUG_LEVEL1
    if args.D:
        debug=DEBUG_LEVEL2
    if args.A:
        debug=DEBUG_LEVEL3
    if args.r:
        retry = True
    if args.i: 
       mqtt_broker_ip_cmdline = args.i
 
    return(args)

#----------------------------------------------------------
# ***** Function reboot läuft als Thread **************************
def reboot_function():  #   --> in eigenem Thread !!

    while True:
        if reboot_verlangt:
            print ("swserver3 terminating mit reboot pi")
            time.sleep(10)      # give switcher3 time to switch of dosen
            os.system('sudo reboot') 
          #        
        elif shutdown_verlangt:
    
            time.sleep(10)  # give switcher3 time to switch of dosen
            os.system('sudo shutdown -r now')        
        else: 
            time.sleep(1)    


#----------- Function to reag switcher log ---------------
def do_getlog():

    zeilen = []

  # find switcher processes and their pid
    procsli = find_procs_by_name ("python3")
    # we do  not need the reurn list
    # ok, dies ist versorgt im Log
    # nun tail commend ausführen

    command = "tail -n 300 " + path + "/" + logfile_name
    p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
 
    (output, err) = p.communicate()
    p_status = p.wait()
    if p_status > 0:
        myprint.myprint (DEBUG_LEVEL0, progname +  "Fehler nach tail command ausführung:{}".format(p_status))
    
    #  damit auch alle chars kommen...
    # https://stackoverflow.com/questions/21129020/how-to-fix-unicodedecodeerror-ascii-codec-cant-decode-byte
    if isinstance(output, str):
        output = output.decode('ascii', 'ignore').encode('ascii') #note: this removes the character and encodes back to string.
    elif isinstance(output, str):
        output = output.encode('ascii', 'ignore')
    
    
    if type(output) is str:
#        print ("type ist str")
        pass
    else:
        try:
            output = output.decode()
        except:
            myprint.myprint (DEBUG_LEVEL1, progname + "log string kann nicht decodiert werden\nEnthaelt ev. Umlaute")
            output = "Fehler im Server:\nswitcher3.log string kann nicht decodiert werden\nEnthaelt ev. Umlaute"
#    print ("Command output : ", output)
#    print ("Command exit status/return code : ", p_status)
    zeilen = list(output.split("\n"))   # convert string mit NewLine into list

    return(zeilen)


#--------------------------------------------
# get pid für switcher3 programme
def find_procs_by_name(name):

    "Return a list of processes matching 'name'."
    ls = []         # set list
    for p in psutil.process_iter(["pid", "name", "exe", "cmdline", "num_threads"]):
        if name == p.info['name'] or \
                p.info['exe'] and os.path.basename(p.info['exe']) == name or \
                p.info['cmdline'] and p.info['cmdline'][0] == name:
            
            ls.append ([p.info['pid'],p.info['cmdline'][-1], p.info['cmdline'][-2], p.info['num_threads']] )

    for pr in ls:
        # print ("")
        # print (pr)
        for i, item in enumerate(pr):
        
            print ("item[{}]:{}".format(i,item))
            if type(item) == str and item.find("switcher3.py") != -1:
            #    print ("switcher3 pid:{}, threads:{}".format(pr[0], pr[3]))
                swi_pid = pr[0]
                swi_thr = pr[3]
            if type(item) == str and item.find("swserver3.py") != -1:
            #    print ("swserver3 pid:{}, threads:{}".format(pr[0], pr[3]))
                swser_pid = pr[0]
                swser_thr = pr[3]
        # return list

    if swser_pid > 0:
        myprint.myprint (DEBUG_LEVEL0, progname +  "swserver3 running pid:{}, threads:{}".format(swser_pid, swser_thr))  
    else:
        myprint.myprint (DEBUG_LEVEL0,  progname +  "swserver3 prozess nicht gefunden")  
    
    if swi_pid > 0:
        myprint.myprint (DEBUG_LEVEL0, progname +  "switcher3 running pid:{}, threads:{}".format(swi_pid, swi_thr))
    else:
        myprint.myprint (DEBUG_LEVEL0,  progname +  "switcher3 prozess nicht gefunden")  

    return ([swi_pid,swi_thr,swser_pid,swser_thr])



#-------------------------------------------------
# get hostname und IP
#----------------------------------------------
def get_Host_name_IP():
    try:
        host_name = socket.gethostname()
        host_ip = socket.gethostbyname(host_name + ".local")
    except:
        print("Unable to get Hostname and IP")
    
    return (host_name, host_ip)


#----------------------------------------------
# check mqtt status
#----------------------------------------------

def check_mqtt():
    
    error_return = 0

 # check mqtt status
    mqtt_connect, mqtt_error = swconnector.mqtt_status()
    if mqtt_connect == False:
        myprint.myprint (DEBUG_LEVEL0, progname +  "Keine mqtt Connection möglich")
        error_return = MQTT_ERROR
    
    return (error_return)

#--------------------------------------------------------
# handle incoming messages from switcher3 (with MQTT_TOPIC_SUBSERV)
#---------------------------------------------------------
def notifyServer (art,message_in):
    global  terminate

    myprint.myprint (DEBUG_LEVEL1, progname +  ": notifyServer called:{}". format(message_in))
   # print (message[0])
   # print (message[1])
#   switcher meldet, was er gemacht hat 
#   message[2] enthält auto oder manuell, je nach dem, warum das device geschaltet wurde
#
    message =[]
    cmd = message_in.pop(0)
    myprint.myprint (DEBUG_LEVEL2, progname + "Command ist:{}, message_in:{}".format(cmd, message_in))
    
    for item in message_in[0]:  
        message.append(item)

    if (cmd == "done_dev"): 
       # for item in message_in[0]:  
        #    message.append(item)

        myprint.myprint (DEBUG_LEVEL2, progname + "message_in: {}".format(message))
        if message[0] == 1:   # dose 1
            myprint.myprint (DEBUG_LEVEL3, progname + "do socket_io dose 1")
            socketio.emit('dev1_change', { 'estateb': message[1], 'estatet': message[2], 'istateb': message[3], 'istatet': message[4],   \
                                           'modusb': message[5], 'modust': message[6], 'typ': message[7], 'art': message[8], 'room': message[9]} )     #    index 1 is extern state
        
        elif message[0] == 2:  
            myprint.myprint (DEBUG_LEVEL3, progname + "do socket_io dose 2")
            socketio.emit('dev2_change', { 'estateb': message[1], 'estatet': message[2], 'istateb': message[3], 'istatet': message[4],   \
                                           'modusb': message[5], 'modust': message[6], 'typ': message[7], 'art': message[8], 'room': message[9]} )     #    index 1 is extern state

        elif message[0] == 3: 
            myprint.myprint (DEBUG_LEVEL3, progname + "do socket_io dose 3")
            socketio.emit('dev3_change', { 'estateb': message[1], 'estatet': message[2], 'istateb': message[3], 'istatet': message[4],   \
                                           'modusb': message[5], 'modust': message[6], 'typ': message[7], 'art': message[8], 'room': message[9]} )     #    index 1 is extern state

        elif message[0] == 4:  
            myprint.myprint (DEBUG_LEVEL3, progname + "do socket_io dose 4")
            socketio.emit('dev4_change', { 'estateb': message[1], 'estatet': message[2], 'istateb': message[3], 'istatet': message[4],   \
                                           'modusb': message[5], 'modust': message[6], 'typ': message[7], 'art': message[8], 'room': message[9]} )     #    index 1 is extern state

        elif message[0] == 5:  
            myprint.myprint (DEBUG_LEVEL3, progname + "do socket_io dose 5")
            socketio.emit('dev5_change', { 'estateb': message[1], 'estatet': message[2], 'istateb': message[3], 'istatet': message[4],   \
                                           'modusb': message[5], 'modust': message[6], 'typ': message[7], 'art': message[8], 'room': message[9]} )     #    index 1 is extern state


    elif cmd == "done_home":  
        myprint.myprint (DEBUG_LEVEL3, progname + "do socket_io home switch")
        # Broadcast a switch change event.
        socketio.emit('change_switch_server', { 'switchb': message[0], 'switcht': message[1]})


    elif cmd == "all_reset":  
        myprint.myprint (DEBUG_LEVEL3, progname + "do socket_io all_reset")
        # Broadcast events.
        socketio.emit('change_switch_server', { 'switch': 0} )
        socketio.emit('dev1_change', { 'dev1_state': 0}) 
        socketio.emit('dev2_change', { 'dev2_state': 0 })    
        socketio.emit('dev1_state_change', { 'dev1_state': 0}) 
        socketio.emit('dev2_state_change', { 'dev2_state': 0}) 
    else:
        myprint.myprint (DEBUG_LEVEL0, progname +  ": invalid message_in received: {}". format(message))

#-------------------------------------------------------------  
#- do publish  to switcher3
#-------------------------------------------------------------       
def messageOut (meldung):
    myprint.myprint (DEBUG_LEVEL1, progname + ": messageOut: {} ".format(meldung))
    payl=json.dumps(meldung)          # umwandeln in JSON Object (also ein String)    
   
    swconnector.transmit (payl) 
   
 #  mqtt_error = mqttc.publish_msg (MQTT_TOPIC_PUBSWIT, payl)
 #   if (mqtt_error > 0):
 #       myprint.myprint (DEBUG_LEVEL0,  "publish returns: {} ".format(mqtt_error))

#--------------------------------------------
#   tue etwas und gebe dann output zurück 
#   dies wird dann in html code eingesetzt

#-------------------------------------------------------------  
#  set anzahl dosen 
#-------------------------------------------------------------  
def set_anzdosen (anzahl):
    meld2 = []
    retco = []

    text = "Neue Anzahl Dosen gesetzt, Reboot Switcher, bitte warten..."
    
    myprint.myprint (DEBUG_LEVEL1, "set_anzdosen() called, reset: {}".format(anzahl))
    
    
    message = "dos" + str(anzahl)
  
    return(0,0)     


#-----------------------------------------------------
# Setup function
# setup the Server
# -----------------------------------------------------
def setup_server():
    global mqttc, myprint, mqtt_connect, path
    global reboot_verlangt, swconnector
    global host_name, host_ip, debug

    error_return = 0            # return code setup function

    argu()                          # get commandline argumants
    
    path = os.path.dirname(os.path.realpath(__file__))    # current path
 #   pfad = os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft


# create Instance of MyPrint Class 
    myprint = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  path + "/" + logfile_name ) 
  
    myprint.myprint (DEBUG_LEVEL0,  progname + "started <---------------------: {}".format(time.strftime('%X')))   
    myprint.myprint (DEBUG_LEVEL0,  progname + "Name logfile: {} ".format( path + "/" + logfile_name) )
    myprint.myprint (DEBUG_LEVEL0,  progname +  "Name configfile: {} ".format( path + "/" + configfile_name) ) 

    # Red Configfile --------------------
    # Create Instance of the ConfigRead Class
    myconfig = ConfigRead(debug_level = debug)     

    myprint.myprint (DEBUG_LEVEL3,  progname + "Configdictionary before reading:")
    if (debug > 2):
        for x in cfglist_swi:
            print ("{} : {}".format (x, cfglist_swi[x]))

    # Read from Configfile  
    ret = myconfig.config_read (path+"/" + configfile_name ,config_section, cfglist_swi)  # call method config_read()
    myprint.myprint (DEBUG_LEVEL1, progname + "config_read() returnvalue: {}".format (ret))	# für log und debug
 
    myprint.myprint (DEBUG_LEVEL3, progname + "Configdictionary after reading:")
    if (debug > 2):
        for x in cfglist_swi:
            print ("{} : {}".format (x, cfglist_swi[x]))
         
    if ret > 0 :
        print ("swserver3 terminate after configread")
        sys.exit(2)     # xxx   anpassen !!

    # wenn gpio blink angegeben ist (ungleich 0) starten wir den Blink Thread <<---

    try:
        debug_konf =        int(cfglist_swi["debug"])            # debug flag aus konfigfile
    except KeyError :
            myprint.myprint (DEBUG_LEVEL0, progname + "KeyError in cfglist_swi, check values!")   

    if debug_konf > 0:
        myprint.myprint (DEBUG_LEVEL0, progname + "debug verlangt in configfile, wert:{}".format(debug_konf))
    if debug == 0: 
        debug = debug_konf
    myprint.set_debug_level(debug)          # set level in the myPrint object

    # fertig lesen config file ----------------------
    # get hostname und IP Adr
    host_name, host_ip = get_Host_name_IP()
    myprint.myprint (DEBUG_LEVEL0,  progname +  "hostname/IP/Version:{}/{}/{}".format( host_name, host_ip,server_version) ) 
    #------------------------------------
    #  create Instance of SwConnector Class  
    swconnector = SwConnector ( debug = debug, 
                                path = path,
                                configfile = configfile_name,
                                endpoint = 2,
                                mqtt_client = None,
                                callback = notifyServer)
    time.sleep(1)    


    myprint.myprint (DEBUG_LEVEL0 ,progname +  "object created: {}".format(swconnector))
    
    # check mqtt status
    error_return = check_mqtt()
    if error_return > 0:
        error_return = MQTT_ERROR

    else:
        # init for receiving of sync messages (only needed on client (SWSERVER) side)
        swconnector.request_response_init (MQTT_TOPIC_RESP)


    # init for receiving of sync messages (only needed on client side)
    swconnector.request_response_init (MQTT_TOPIC_RESP)
# aufsetzen und starten des reboot threads

    reboot_thread = threading.Thread(target=reboot_function)
    reboot_thread.setDaemon (True)                      # damit thread beendet wird, wenn main thread endet
    reboot_thread.start()
  
    count_thread = threading.active_count()
    thread_list = threading.enumerate()
        
    myprint.myprint (DEBUG_LEVEL1,  progname + "Anzahl Threads: {},  List: {}".format(count_thread,thread_list))
    myprint.myprint (DEBUG_LEVEL0,  progname +  "--> gestartet")
    myprint.myprint (DEBUG_LEVEL0,  progname +  "setup Server done")

    return(error_return)
# end setup    
#---------------------------------------------------------


# --------------------------------------------------------
# Define app routes.
# --------------------------------------------------------
#
# Index route renders the main HTML page.
# --------------------------------------------------------
@app.route('/index.html', methods=['GET', 'POST'])
@app.route("/")
def home():
    global home_state_b, home_state_t ,initial_data, anzahl_dosen_definiert,switcher_version


    info_list = []
    
    myprint.myprint (DEBUG_LEVEL1,  progname +  "app.route /index called")   
   
    # check mqtt status vor dem Senden
    # falls fehlerhaft, gebe Error seite aus
    error_return = check_mqtt()
    if error_return > 0:
        error_return = MQTT_ERROR
        myprint.myprint (DEBUG_LEVEL0,  progname +  "check_mqtt returns:{}".format(error_return))  
        return render_template('status.html',  show_reboot = False, error_text_1 = "MQTT Error, kann nicht senden, check Log")



    send_request = "{:10}".format("home")
    ret, response_request, msg_return = swconnector.transmit_sync ( send_request, TIMEOUT_SYNC)
        #  response_request:    contains the request_string sent to switcher3
        #  msg_return:          contains a list of three lists
        #                       msg_return[0] is list of switcher data (version) 
        #                       msg_return[1]  is list of 6 items for top of index.html page
        #                       msg_return[2]  is list of 2 lists 
        #                       msg_return[2][0] is home state  int
        #                       msg_return[2][1] is home state Text
        #                       msg_return[2][1] is list of dosenstati
    answer_ok = False

    if ret == 0:
        answer_ok = True
    elif ret == 9:
        myprint.myprint (DEBUG_LEVEL1,  progname +  "transmit_sync() returned timeout: {}".format(ret))
    else:
        myprint.myprint (DEBUG_LEVEL1,  progname +  "transmit_sync() returned other error: {}".format(ret))
            
    if answer_ok:
      #  myprint.myprint (DEBUG_LEVEL1,  "msg_sync () returned this msg: {}".format(msg_return))
        myprint.myprint (DEBUG_LEVEL1,  progname +   "app_route index: answer OK")
                # or do something appropiate
        time.sleep(1)
    else:
          return render_template('status.html',  show_reboot = False, error_text_1 = "Keine Antwort von Switcher, siehe LogFiile")

    
    #--------------- Home, also index.html -----------------------------------
    initial_data = []  # MAKE EMPTY
    if response_request.find("home") == 0:              # we get a response with string home, seems ok at this point

        switcher_version    = msg_return [0][0]
        anzahl_dosen_definiert = msg_return [0][1]

        if debug > 1:
            for item in msg_return[1]:                 #   d6 fields for top of page
                print ("item:{}".format(item))
            for item in msg_return[2][1]:             #   device info (list)
                print ("item:{}".format(item))

        for item in msg_return[2][1]:             #   device info (list)
            initial_data.append(item)              #  fill list initial data 
            myprint.myprint (DEBUG_LEVEL2,  progname +   "item in initial_data:{}".format(item))

        for item in msg_return[1]:
            info_list.append("{:<19} {:>18}".format(item[0]  + ": " ,item[1] ))

        home_state_t = msg_return[2][0][1]         # zuhause niemand zuhause
        home_state_b = msg_return[2][0][0]         # zuhause niemand zuhause

        myprint.myprint (DEBUG_LEVEL2,  progname +  "switcher_version: {}".format(switcher_version)) 
        myprint.myprint (DEBUG_LEVEL2,  progname +  "home state: {}/{}".format(home_state_b, home_state_t))


    myprint.myprint (DEBUG_LEVEL0,  progname +  "going to render index.html")      

   # stat_list = ["asas","asas","rtete","sdfsdfsfd","etrwrewr","tztztzt"]

    # Render index.html template.
 #   return render_template('index.html', home_state = home_state, state1= device_1, state2= device_2)
    if answer_ok:
        return render_template('index.html', info_1_list = info_list, html_file2 = select_dosenanz_htmlfiles [anzahl_dosen_definiert], \
                    version_sw = switcher_version +" / " + server_version)
    else:
        return render_template('index.html', statklein = a_list, html_file2 = select_dosenanz_htmlfiles [anzahl_dosen_definiert])  

#----------------------------------------------
# Callback für log.html   
# die Log Seite wird verlangt
# ACHTUNG: dies wird im server erledigt, switcher braucht man dazu nicht  
#--------------------------------------------
@app.route('/swlog.html')
def log():
    global swi_pid, swser_pid 
    myprint.myprint (DEBUG_LEVEL1,  progname +  "app.route /swlog called")     

 # check mqtt status vor dem Senden
    # falls fehlerhaft, gebe Error seite aus
    error_return = check_mqtt()
    mqtt_string = "MQTT Status OK"

    while error_return > 1:
        myprint.myprint (DEBUG_LEVEL0,  progname +  "check_mqtt returns:{}".format(error_return))  
        myprint.myprint (DEBUG_LEVEL0,  progname +  "trying to reconnect...") 
        swconnector.reconnect()
        time.sleep(1)
        error_return = check_mqtt()
        if error_return >1:
            mqtt_string = "MQTT keine Verbindung möglich"
            break
        else:
            break
       


    time.sleep(.5)
    zeilenlist = do_getlog()
    myprint.myprint (DEBUG_LEVEL0,  progname +  "going to render swlog.html")      

    return render_template('swlog.html',logzeilen = zeilenlist, show_reboot = True, boot_text = bootmsg_1, mqtttext = mqtt_string)


#----------------------------------------------
# Callback für swactionlist.html     
# die Seite mit allen Aktionen wird verlangt
#--------------------------------------------
@app.route('/swactions.html')
def actions():
    myprint.myprint (DEBUG_LEVEL1,  progname +  "app.route /swactions called")     


    now_time = datetime.now()       # aktuelle Zeit holen
  #  zeilenlist = do_getlog()

    # check mqtt status vor dem Senden
    # falls fehlerhaft, gebe Error seite aus
    error_return = check_mqtt()
    if error_return > 0:
        error_return = MQTT_ERROR
        myprint.myprint (DEBUG_LEVEL0,  progname +  "check_mqtt returns:{}".format(error_return))  
        return render_template('status.html',  show_reboot = False, error_text_1 = "MQTT Error, kann nicht senden, check Log")

    past = ["aaa","bbb"]
    future = ["aaa","bbb","cccccc"]
    send_request = "{:10}".format("aliste")
    ret, response_request, msg_return = swconnector.transmit_sync ( send_request, TIMEOUT_SYNC)

    #  THis comes back from switcher3
    #  response_request:  contains the request_string sent to switcher
    #  msg_return:        contains a list of two lists (past actions and future actions)

    answer_ok = False

    if ret == 0:
        answer_ok = True
    elif ret == 9:
        myprint.myprint (DEBUG_LEVEL1,  progname +   "msg_sync () returned timeout: {}".format(ret))
    else:
        myprint.myprint (DEBUG_LEVEL1,  progname +   "msg_sync () returned other error: {}".format(ret))
            
    if answer_ok:
        myprint.myprint (DEBUG_LEVEL1,  progname +   "msg_sync () returned this msg: {}".format(msg_return))
                # or do something appropiate
        time.sleep(1)

    myprint.myprint (DEBUG_LEVEL1,  progname +  "going to render swactionlist.html")      
    
    if response_request.find("aliste") == 0:

#    error behandlung    
        if debug > 1:
            print ("week:{}, adjmin:{}".format(msg_return[0][0], msg_return[0][1]))
            for item in msg_return[0]:          # msg_return[0] is list of past actions
                print (item)
            for item in msg_return[1]:          # msg_return[1] is list of future actions
                print (item)    


   # mu = json.loads(msg_return) 
    if answer_ok:
        return render_template('swactions.html',zeit = now_time.strftime("%H:%M" ), pastactzeilen = msg_return[1], futureactzeilen = msg_return[2] , \
                            adj_info = msg_return[0][0])

    else:
        return render_template('status.html',  show_reboot = False, error_text_1 = "Keine Antwort von Switcher, siehe LogFiile") 
    

#----------------------------------------------
# Callback für swwetter.html     
# die Wetter Seite wird verlangt
#--------------------------------------------
@app.route('/swwetter.html')
def wetter():
    myprint.myprint (DEBUG_LEVEL1,  progname +  "app.route /swwetter called")     

    list_indoor = []                # create empty list for indoor values
    list_outdoor = []               # create empty list for outdoor values

    # check mqtt status vor dem Senden
    # falls fehlerhaft, gebe Error seite aus
    error_return = check_mqtt()
    if error_return > 0:
        error_return = MQTT_ERROR
        myprint.myprint (DEBUG_LEVEL0,  progname +  "check_mqtt returns:{}".format(error_return))  
        return render_template('status.html',  show_reboot = False, error_text_1 = "MQTT Error, kann nicht senden, check Log")

    send_request = "{:10}".format("wetter")
    ret, response_request, msg_return = swconnector.transmit_sync ( send_request, TIMEOUT_SYNC)

    #  THis comes back from switcher3
    #  response_request:  contains the request_string sent to switcher
    #  msg_return:        contains a list of two lists (configured, indoor values, outdoor values)

    answer_ok = False

    if ret == 0:
        answer_ok = True
    elif ret == 9:
        myprint.myprint (DEBUG_LEVEL1,  progname +   "transmit_sync() returned timeout: {}".format(ret))
    else:
        myprint.myprint (DEBUG_LEVEL1,  progname +   "transmit_sync() returned other error: {}".format(ret))
            
    if answer_ok:
        myprint.myprint (DEBUG_LEVEL1,  progname +   "transmit_sync() returned this msg: {}".format(msg_return))
                # or do something appropiate
        time.sleep(0.5)

        if msg_return[0][0] == 0:      # first list 
            print ("wetter nicht konfiguriert")
            return render_template('status.html',  show_reboot = False, error_text_1 = "Wetter ist nicht konfiguriert") 
        else:
            print ("wetter konfiguriert")
        
            msg_return.pop(0)                # erste liste entfernen

            #print (len(msg_return[0]))
            #for i in range(len(msg_return[0][0])):  
            #    print (msg_return[0][0][i])

            myprint.myprint (DEBUG_LEVEL0,  progname +  "going to render swwetter.html")      
            # erste Liste in msg_return[0] sind indoor wetterdaten
            for i in range(len(msg_return[0][0])):             # länge der ersten liste
                myprint.myprint (DEBUG_LEVEL3,  progname +  "{}".format(msg_return[0][0][i]))
                list_indoor.append("{:<19} {:>18}".format(msg_return[0][0][i][0]  + ": " ,msg_return[0][0][i][1] ))

            # zweite Liste in msg_return[0] sind outdoor wetterdaten
            for i in range(len(msg_return[0][1])):
                myprint.myprint (DEBUG_LEVEL3,  progname +  "{}".format(msg_return[0][1][i]))
                list_outdoor.append("{:<19} {:>18}".format(msg_return[0][1][i][0]  + ": " ,msg_return[0][1][i][1] ))
     

 
            myprint.myprint (DEBUG_LEVEL1,  progname +  "going to render swwetter.html")     
            return render_template('swwetter.html', indoor_list = list_indoor, outdoor_list = list_outdoor)


    else:
        return render_template('status.html',  show_reboot = False, error_text_1 = "Keine Antwort von Switcher, siehe LogFiile") 
    
      
    

 #----------------------------------------------
# Callback für swinfo.html    
# Die Info Seite wird verlangt 
#--------------------------------------------
@app.route('/swinfo.html')
def info():
    myprint.myprint (DEBUG_LEVEL1,  progname +  "app.route /swinfo called")     

 
    # check mqtt status vor dem Senden
    # falls fehlerhaft, gebe Error seite aus
    error_return = check_mqtt()
    if error_return > 0:
        error_return = MQTT_ERROR
        myprint.myprint (DEBUG_LEVEL0,  progname +  "check_mqtt returns:{}".format(error_return))  
        return render_template('status.html',  show_reboot = False, error_text_1 = "MQTT Error, kann nicht senden, check Log")


    send_request = "{:10}".format("info")
    ret, response_request, msg_return = swconnector.transmit_sync ( send_request, TIMEOUT_SYNC)

    #  THis comes back from switcher3
    #  response_request:  contains the request_string sent to switcher
    #  msg_return:        contains a list of two list 
    #                       first list is empty (future use)
    #                       second list contains all info items
    answer_ok = False
    info_list = []
    if ret == 0:
        answer_ok = True
    elif ret == 9:
        myprint.myprint (DEBUG_LEVEL1,  progname +   "transmit_sync() returned timeout: {}".format(ret))
    else:
        myprint.myprint (DEBUG_LEVEL1,  progname +   "transmit_sync() returned other error: {}".format(ret))
            
    if answer_ok:
        myprint.myprint (DEBUG_LEVEL1,  progname +   "transmit_sync() returned this msg: {}".format(msg_return))
                # or do something appropiate
        for item in msg_return[1]:
            info_list.append("{:<19} {:>18}".format(item[0]  + ": " ,item[1] ))


     
    
    if response_request.find("aliste") == 0:

#    error behandlung    
        if debug > 1:
            for item in msg_return[1]:          # msg_return[0] is list of info items
                print (item)

    
    if answer_ok:
        myprint.myprint (DEBUG_LEVEL1,  progname +  "going to render info.html")     
        return render_template('swinfo.html', info_2_list = info_list)

    else:
        return render_template('status.html',  show_reboot = False, error_text_1 = "Keine Antwort von Switcher, siehe LogFiile") 
    
      

#----------------------------------------------
# Callback für reboot  
# Reboot Button wurde geklickt   
#--------------------------------------------
@app.route('/reboot.html', methods=['GET', 'POST'])
def reboot():
    global reboot_verlangt
    
    myprint.myprint (DEBUG_LEVEL1,  progname + "app.route /reboot called")     

    cmd = "sudo systemctl stop switcher3.service"
    ret = os.system(cmd)
    time.sleep(2)
   # hier reboot thread benachrichtigen
    reboot_verlangt = True

    myprint.myprint (DEBUG_LEVEL1,  progname +  "going to render resultat.html (2)")    
                         # resultat.html ausgeben mit Angabe der gemachten Aktion
    return render_template('status.html', show_reboot = False, error_text_1 = bootmsg_2, error_text_2 = "")

#----------------------------------------------
# Callback für shutdown     
# Shut Down Button wurde geklickt
#--------------------------------------------
@app.route('/shutdown.html', methods=['GET', 'POST'])
def shutdown():
    global shutdown_verlangt
    
    myprint.myprint (DEBUG_LEVEL0,  progname + "app.route /shutdown called")     
    myprint.myprint (DEBUG_LEVEL0,  progname + "stop switcher3, then shutdown") 
    cmd = "sudo systemctl stop switcher3.service"
    ret = os.system(cmd)
    time.sleep(2)
   # hier reboot thread benachrichtigen
    shutdown_verlangt = True
    myprint.myprint (DEBUG_LEVEL1,  progname +  "going to render resultat.html (3)")    
                         # resultat.html ausgeben mit Angabe der gemachten Aktion
    return render_template('status.html', show_reboot = False, error_text_1 = bootmsg_3, error_text_2 = "")


#----------------------------------------------
# Callback für swdosen.html     
# Es wird eine Html Seite mit der aktuellen Anzahl Dosen verlangt
#--------------------------------------------
@app.route('/swdosen.html', methods=['GET', 'POST'])
def swdosen():
    global swdosconf

    myprint.myprint (DEBUG_LEVEL1,  progname +  "app.route /swdosen called")     

    if swdosconf == None:
        swdosconf = SWDos_conf (debug = debug, path = path)   # instanz der Klasse erstellen

    zahl = swdosconf.read_dosenconfig()
    return render_template('dosenset.html',anzahl_dosen = zahl)


#----------------------------------------------
# Callback für set_dosem.html     
# Der benutzer hat eine neue Anzahl Dosen ausgewählt
# diese Anzahl wird im Config File der Dosen abgelegt.
# File: swdosen.ini  (in Klasse SWDos_conf erledigt)
#--------------------------------------------
@app.route('/set_dosen.html', methods=['GET', 'POST'])
def set_dosen():
    global swdosconf, reboot_verlangt
    myprint.myprint (DEBUG_LEVEL1,  progname +  "app.route /set_dosen called")     

    if swdosconf == None:
        swdosconf = SWDos_conf (debug = debug, path = path)   # instanz der Klasse erstellen

   
#  das input felder (anzahl dosen untersuchen, schauen, was gekommen ist.   
#   
    ret = 0
    try:
        dosenanz = int(request.form['anzahl_dosen'])
        myprint.myprint (DEBUG_LEVEL1, "Anzahl Dosen neu: {}". format(dosenanz) )   
    
        zahl = swdosconf.read_dosenconfig()
        print ("Gelesen Anzahl Dosen:{}".format(zahl))
        print ("Schreiben Anzahl:{}".format(dosenanz))
        ret = swdosconf.write_dosenconfig(dosenanz)

    except:
        error0 = True
        myprint.myprint (DEBUG_LEVEL1, "Input check: anzahl_dosen nichts gekommen")
    
 
    myprint.myprint (DEBUG_LEVEL1, "going to render status.html (4)")    
    
    if ret == 0:                    # zero means : anzahl war schon wie gehabt, wurde nichts verändert 
        text_1 = "Anzahl Dosen nicht verändert, war schon gesetzt"
    else:
        text_1 = "Neue Anzahl Dosen: {}".format (ret)
    
        myprint.myprint (DEBUG_LEVEL0,  progname + "stop switcher3, then reboot") 
        cmd = "sudo systemctl stop switcher3.service"
        ret = os.system(cmd)
        time.sleep(10)
        reboot_verlangt = True
    
    return render_template('status.html',  show_reboot = False, error_text_1 = text_1, error_text_2 = "Switcher3 wird neu gebootet")      
   





# --------------------------------------------------------
# socket io events coming in from client (webpage in browser)
# diese Event werden gesendet, wenn der Benutzer einen Button au der Webseite klickt
# es gibt verschiedene Buttons und deshalb auch verschiedene Events
#---------------------------------------------------------

#-----------------------------------------------------
# Listen for SocketIO event that requests initial data
# wird gesendet, wenn die Home Page neu geladen worden ist
# alle aktuellen Schaltzustände werden an den Browser gesendet
#--------------------------------------------------------
@socketio.on('get_initial')
def get_initial(p1):

    myprint.myprint (DEBUG_LEVEL3, progname + ": get_initial on socket: {}".format(p1))

    # zuhause behandlen
    myprint.myprint (DEBUG_LEVEL1,  progname + "home state: {}/{}".format(home_state_b, home_state_t))
    socketio.emit('change_switch_server', { 'switchb': home_state_b, 'switcht': home_state_t})

    for devicenummer, device in enumerate(initial_data): 
        devicenummer += 1           # 0 ist dose 1 !!
        myprint.myprint (DEBUG_LEVEL2,  progname + "item in initial_data,device:{}, data:{}".format(devicenummer, device))
        if devicenummer == 1:
            socketio.emit('dev1_change', { 'estateb': device[1], 'estatet': device[2], 'istateb': device[3], 'istatet': device[4],   \
                                           'modusb': device[5], 'modust': device[6], 'typ': device[7], 'art': device[8], 'room': device[9]} )     #    index 1 is extern state
                 
        if devicenummer == 2:
            socketio.emit('dev2_change', { 'estateb': device[1], 'estatet': device[2], 'istateb': device[3], 'istatet': device[4],   \
                                           'modusb': device[5], 'modust': device[6], 'typ': device[7], 'art': device[8], 'room': device[9]} )     #    index 1 is extern state

        if devicenummer == 3:
            socketio.emit('dev3_change', { 'estateb': device[1], 'estatet': device[2], 'istateb': device[3], 'istatet': device[4],   \
                                           'modusb': device[5], 'modust': device[6], 'typ': device[7], 'art': device[8], 'room': device[9]} )     #    index 1 is extern state     

        if devicenummer == 4:
            socketio.emit('dev4_change', { 'estateb': device[1], 'estatet': device[2], 'istateb': device[3], 'istatet': device[4],   \
                                           'modusb': device[5], 'modust': device[6], 'typ': device[7], 'art': device[8], 'room': device[9]} )     #    index 1 is extern state  

        if devicenummer == 5:
            socketio.emit('dev5_change', { 'estateb': device[1], 'estatet': device[2], 'istateb': device[3], 'istatet': device[4],   \
                                           'modusb': device[5], 'modust': device[6], 'typ': device[7], 'art': device[8], 'room': device[9]} )     #    index 1 is extern state

# --------------------------------------------------------------------
# Eventhandler für socket.io
#----------------------------------------------------------------------
# Listen for SocketIO event that will toggle device 1
# Benutzer hat Button für dose 1 geklickt
@socketio.on('dev1_toggle')
def toggle_dev1(led):
    global device_1
    myprint.myprint (DEBUG_LEVEL1, progname + ":change dev1 on socket, led: {}". format(led))

 #   note: socketio.emit wird erst beim eintreffen mqtt message vom switcher gemacht (
    meldung = ["tog_dev", 1, 0,0 ]   # note the double round-bracketsta  
    messageOut ( meldung )

#-----------------------------------------------------
# Listen for SocketIO event that will toggle the device_2
# Benutzer hat Button für dose 2 geklickt
@socketio.on('dev2_toggle')
def toggle_dev2(led):
    global device_2
    myprint.myprint (DEBUG_LEVEL1, progname + ": change dev2 on socket, led: {}". format(led))

#   note: socketio.emit wird erst beim eintreffen mqtt message vom switcher gemacht (
    meldung = ["tog_dev", 2,0,0]    # note the double round-bracketsta  
    messageOut ( meldung )

#-----------------------------------------------------
# Listen for SocketIO event that will toggle the device_3
# Benutzer hat Button für dose 3 geklickt
@socketio.on('dev3_toggle')
def toggle_dev3(led):
    global device_3
    myprint.myprint (DEBUG_LEVEL1, progname + ": change dev3 on socket, led: {}". format(led))

#   note: socketio.emit wird erst beim eintreffen mqtt message vom switcher gemacht (
    meldung = ["tog_dev", 3,0,0]    # note the double round-bracketsta  
    messageOut ( meldung )

 #-----------------------------------------------------
# Listen for SocketIO event that will toggle the device_4
# Benutzer hat Button für dose 4 geklickt
@socketio.on('dev4_toggle')
def toggle_dev4(led):
    global device_4
    myprint.myprint (DEBUG_LEVEL1, progname + ": change dev4 on socket, led: {}". format(led))

#   note: socketio.emit wird erst beim eintreffen mqtt message vom switcher gemacht (
    meldung = ["tog_dev", 4,0,0]    # note the double round-bracketsta  
    messageOut ( meldung )   

#-----------------------------------------------------
# Listen for SocketIO event that will toggle the device_5
# Benutzer hat Button für dose 5 geklickt
@socketio.on('dev5_toggle')
def toggle_dev5(led):
    global device_5
    myprint.myprint (DEBUG_LEVEL1, progname + ": change dev5 on socket, led: {}". format(led))

#   note: socketio.emit wird erst beim eintreffen mqtt message vom switcher gemacht (
    meldung = ["tog_dev", 5,0,1,0, "tomato"]    # note the double round-bracketsta  
    messageOut ( meldung )   


#-----------------------------------------------------
# Listen for SocketIO event that will toggle the device_1
# Benutzer hat Toggle auto Button für dose 1 geklickt
@socketio.on('dev1_auto')
def dev5_auto(led):
    global device_1
    myprint.myprint (DEBUG_LEVEL1, progname + ": dev1_auto on socket: {}".format(led))
    meldung = ["auto", 1,0,0]   # note the double round-bracketsta  
    messageOut ( meldung )

#-----------------------------------------------------
# Listen for SocketIO event that will toggle the device_2
# Benutzer hat Toggle auto Button für dose 2 geklickt
@socketio.on('dev2_auto')
def dev5_auto(led):
    global device_2
    myprint.myprint (DEBUG_LEVEL1, progname + ": dev2_auto on socket: {}".format(led))
    meldung = ["auto", 2,0,0]   # note the double round-bracketsta  
    messageOut ( meldung )

#-----------------------------------------------------
# Listen for SocketIO event that will toggle the device_3
# Benutzer hat Toggle auto Button für dose 3 geklickt
@socketio.on('dev3_auto')
def dev5_auto(led):
    global device_3
    myprint.myprint (DEBUG_LEVEL1, progname + ": dev3_auto on socket: {}".format(led))
    meldung = ["auto", 3,0,0]   # note the double round-bracketsta  
    messageOut ( meldung )    

#-----------------------------------------------------
# Listen for SocketIO event that will toggle the device_4
# Benutzer hat Toggle auto Button für dose 4 geklickt
@socketio.on('dev4_auto')
def dev5_auto(led):
    global device_4
    myprint.myprint (DEBUG_LEVEL1, progname + ": dev4_auto on socket: {}".format(led))
    meldung = ["auto", 4,0,0]   # note the double round-bracketsta  
    messageOut ( meldung )    

#-----------------------------------------------------
# Listen for SocketIO event that will toggle the device_5
# Benutzer hat Toggle auto Button für dose 5 geklickt
@socketio.on('dev5_auto')
def dev5_auto(led):
    global device_5
    myprint.myprint (DEBUG_LEVEL1, progname + ": dev5_auto on socket: {}".format(led))
    meldung = ["auto", 5,0,0]   # note the double round-bracketsta  
    messageOut ( meldung )


#-----------------------------------------------------
# Listen for SocketIO event that will set auto_all
# Benutzer hat Toggle auto all button geklickt
@socketio.on('auto_all')
def auto_all(led):
    global device_2
    myprint.myprint (DEBUG_LEVEL1, progname + ": auto_all on socket: {}".format(led))
    meldung = ["all_auto", 0,0,0]   # note the double round-bracketsta  
    messageOut ( meldung )

#-----------------------------------------------------
# Listen for SocketIO event that will set all to ON
# Benutzer hat Toggle All ON Button geklickt
@socketio.on('on_all')
def on_all(led):
    global device_2
    myprint.myprint (DEBUG_LEVEL1, progname + ": on_all on socket: {}".format(led))
    meldung = ["all_on", 0,0,0]    # note the double round-bracketsta  
    messageOut ( meldung )

#-----------------------------------------------------
# Listen for SocketIO event that will set all OFF
# Benutzer hat Toggle All OFF Button geklickt
@socketio.on('off_all')
def off_all(led):
    global device_2
    myprint.myprint (DEBUG_LEVEL1, progname + ": OFF_all on socket: {}".format(led))
    meldung = ["all_off", 0,0,0]    # note the double round-bracketsta  xxx
    messageOut ( meldung )    
#-----------------------------------------------------
# Listen for SocketIO event that will change the home switch
# comes from webpage
# Benutzer hat Toggle Daheim Button geklickt
@socketio.on('change_switch_client')
def change_switch(switch):
    myprint.myprint (DEBUG_LEVEL1, progname + ": change switch on socket from client")
 
 #   note: socketio.emit wird erst beim eintreffen mqtt message vom switcher gemacht (
    meldung = ["tog_home", 0,0,0]    # note the double round-bracketsta  
    messageOut ( meldung )                          # send change event to switcher3




#-----------------------------------------------------------
# program starts here
#--------------------------------------------------------
if __name__ == "__main__":


    # do setup fuction
    general_error = setup_server()
    myprint.myprint (DEBUG_LEVEL1 ,progname +  "Setup returns:{}".format (general_error))
   
   # general_error is later used if html pages are requested
    
  
    # Run the flask development web server with SocketIO.
    if (debug > 0):
        myprint.myprint (DEBUG_LEVEL0, progname + ": start flask with debug")
        socketio.run(app, host='0.0.0.0', debug=True, port=4000)
    else:
        myprint.myprint (DEBUG_LEVEL0, progname + ": start flask WITHOUT debug")
        socketio.run(app, host='0.0.0.0', debug=False, port=4000)

#  end of code --------------------------------
