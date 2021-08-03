#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class Aktor_3 
#   
#   Diese Class impmentiert das pyhsische Schalten der Dosen 
#
#   diese Class erbt von der MyPrint Class
#   
#   Version IoT mit Subscribe to MQTT broker.
#   Instanz einer MQTT_Conn muss übergeben werden bei der Creation einer Instanz
#   
#   Alles, was MQTT betrifft wird in der MQTT_Conn Klasse erledigt.
#
#   folgende public methods stehen zur Verfügung:
#       schalten (ein_aus)     ein_aus ist entweder 0 oder 1
#   
#   Juli 2018
#************************************************
#
import os
import sys
import time
from time import sleep
import RPi.GPIO as GPIO         #  Raspberry GPIO Pins
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.myconfig import ConfigRead
import socket
import paho.mqtt.client as mqtt
 
DEBUG_LEVEL0 = 0                      
DEBUG_LEVEL1 = 1
DEBUG_LEVEL2 = 2
DEBUG_LEVEL3 = 3

OFFON = ['AUS','EIN']
OFFON2 = ['OFF','ON']           # für payload mqtt
progname = "swc_aktor3 "


# Publish and subscribe Topic für Smart Switches
# NOte: first element must be present and ''

TOPIC_P = ['','cmnd/dose%/POWER', 'cmnd/future1',' ',' ']  # 4 Topics Publish fuer 4 verschiedene WiFi Schalter
                                                        # item 0 not used !!
TOPIC_S = ['','stat/dose%/POWER', 'stat/future',' ',' ']  # 4 Topics  Subscribe fuer 4 verschiedene WiFi Schalter

# Topic last will der Temp Sensoren                
TOPIC_LW  = "switcher3/switch/lw"

config_section = "aktor_3"                
# ***** Variables *****************************
#   Struktur (Directory) der Daten, die aus dem Configfile swconfig.ini gelesen werden
#   hier die defaultwerte der 'variablen'
cfglist_akt = {
        "placeholder" : " ",
}                                                         # item 0 not used !!
#----------------------------------------------------
# Class Definition Aktor, erbt vom MyPrint
#----------------------------------------------------
class Aktor_3 (MyPrint):
    ' klasse aktor '
    aktorzahler=0               # Class Variable
    
    def __init__(self, dosennummer,debug_in, meldungs_typ, subscribe, config_filename_in, mqtt_client_in, callback_dosen):  # Init Funktion
        self.errorcode = 8           # init wert beliebig aber not zero
        self.nummer = Aktor_3.aktorzahler
        self.debug = debug_in
        self.mqttc = mqtt_client_in
        self.meldungs_typ = meldungs_typ             # typ der mqtt meldung und topic
        self.subscribe_noetig = subscribe
        self.config_file = config_filename_in          # configfile
        self.dosencallback = callback_dosen
        self.dosennummer = dosennummer            # arbeite für diese Dose (1 bis n)
        self.mqtt_broker_ip = ""
        self.mqtt_port = 0
        self.mqtt_keepalive_intervall = 0
        self.mqtt_topic = ""
        self.mqtt_client_id = ""
        self.action_type = "mqtt"     # welche art Schalten ist dies hier
        self.how = ''
        self.myprint (DEBUG_LEVEL2,   progname +  "aktor_init called fuer Dose {}, msg_type:{}, subscribe:{}".format (self.dosennummer,self.meldungs_typ, self.subscribe_noetig))
        Aktor_3.aktorzahler += 1            # erhögen aktorzähler

 # nun mqtt Brokder data aus config holen
        
        config = ConfigRead(self.debug)        # instanz der ConfigRead Class
        ret = config.config_read(self.config_file ,config_section, cfglist_akt)
        if ret > 0:
            self.myprint (DEBUG_LEVEL0,  progname + "config_read hat retcode:{}".format (ret))
            self.errorcode = 99
            return None

           # get values fro config file
        try:
        # no values needed ....
            pass
        except KeyError :
            self.myprint (DEBUG_LEVEL0,  progname + "KeyError in cfglist_akt, check values!")   
    

  
        if self.subscribe_noetig > 0:       #   config verlangt, dass wir ein subscribe absetzen, damit die statusmeldungen
                                            #   von smart switches (sonoff) empfangen werden können
                                            #   NOTE: die Callback-Funktione liegt in der Dosenklasse, sie meldet uns
                                            #   den pointer zur funktion
            first, second = TOPIC_S[self.meldungs_typ].split('%')
            topic_subscribe = first + str(self.dosennummer) + second
  
            self.mqttc.subscribe_topic (topic_subscribe , self.dosencallback)     # subscribe to topic
            self.myprint (DEBUG_LEVEL1,   progname + "done mqtt subscription, topic:{} ".format(topic_subscribe))
    
       #     self.mqttc.subscribe_topic (TOPIC_LW , self.last_will)              # subscribe to Last Will Topic der Sensoren

        pass

#-------------------------------------------
# __repr__ function Aktor_3
# 
    def __repr__ (self):

        rep = "Aktor_3 (Für Dose"  + str(self.dosennummer) + "," + self.action_type  + ")"
        return (rep)


# ************************************************** 		

#-------------Terminate Action PArt ---------------------------------------
# cleanup 
#------------------------------------------------------------------------
    def __del__(self):
        self.myprint (DEBUG_LEVEL3,  progname + "del called")
    
        pass



# ***** Function zum setzen GPIO *********************
    def schalten(self,einaus, debug_level_mod):
      
        payload = ""
        
        self.myprint (DEBUG_LEVEL1,  progname + "schalten called:{} ".format(OFFON[einaus]))
        
#       WICHTIG:
#       self.meldungs_typ == 1 ist für Testaufbau mit DIY switches mit esp8266 
#       self.meldungs_typ == 2 ist für sonoff switches , 
#       other smart switches might use other payloads <<<<------------- 
#       subscriber script swmqtt_sub.py zeigt meldung an
#
        self.how = OFFON2[einaus]        # 'ON' oder 'OFF' setzen, wird gebraucht für Payload


        if self.meldungs_typ == 2 or self.meldungs_typ == 1:          # mqtt typ 1 oder 2 für sonoff switches and DIY switches    
 #           self.mqtt_topic = TOPIC_P[self.meldungs_typ]
            first, second = TOPIC_P[self.meldungs_typ].split('%')
            self.mqtt_topic = first + str(self.dosennummer) + second
            payload = self.how              # 'ON' oder 'OFF'

        elif self.meldungs_typ == 3:           # mqtt typ 3  (for future use9)      
            self.mqtt_topic = TOPIC_P[self.meldungs_typ]
            payload = str(self.dosennummer) + self.how
                   
               
        
        
                                    # wir verwenden für loggin den mod debuglevel von der dose
        self.myprint (debug_level_mod,  progname + "publish mqtt Topic:{} , Payload:{}".format(self.mqtt_topic, payload))
 
 
        mqtt_error = self.mqttc.publish_msg (self.mqtt_topic, payload)
#        time.sleep(0.3)
        if mqtt_error > 0:
            self.myprint (DEBUG_LEVEL0,  progname + "publish returns errorcode:{}".format(mqtt_error)) 
        
        return (mqtt_error)       


#---- set_sensorstat -----------------
# hier kommt Last Will and Testament des schalters (siehe Arduino Code für ESP8266)
    def last_will(self,payload):
        self.myprint (DEBUG_LEVEL2, progname +  "last_will() called  payload:{}".format( payload))
        pass
        
        # vorläufig empty
 
#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swc_aktor_3.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
