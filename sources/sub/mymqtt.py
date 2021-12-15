#!/usr/bin/python
# coding: utf-8
# ***********************************************
# ***********************************************************
# 	MQTT Class
#   
#   Encapsulates everything MQTT
#
#   Inherits from MYPrint and ConfigRead Classes
#   provides these Public Methods
#   
#       publish_msg (...)
#       subscribe_topic (..)
#       unsubscribe_topic (..)
#       loop_forever (..)
#       loop_start (..)
#       loop_stop (..)
#       loop()
#       get_status ()
#       reconnect()
#       set_will()
#
#       logs and prints according the the debug parameter
#       0: minimum
#       1: some details
#       2: more details
#       3: everthing that happens
#  
#   original version October 2018 PBX
#   enhanced Sept. 2020
#************************************************
#
import os
import sys
import time
import random
from time import sleep
import paho.mqtt.client as mqtt
import socket
from datetime import date
from sub.myprint import MyPrint             # Class MyPrint
from sub.myconfig import ConfigRead       # Class ConfigRead 


# define debug levels, 0= default, oterh values with commandline parameter -d
DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
CONNECT_COUNTER = 5     # loopp counter für mqtt connection
PUBLISH_COUNTER = 2
#-------------------------------------------------
# Class MQTT_Conn inherits from Class MyPrint and from
#   class ConfigRead 
#--------------------------------------------------
class MQTT_Conn(MyPrint):
    ' class MQTT_Conn '

#    Definition of Class Variables
    instzahler=0           # Class variable Number of  instanzen


#-------Constructor der Klasse ------------------------------------------
# 
#
    def __init__ (self , debug , path , client , ipadr , retry , conf ):
        
    # class instance variables    
        self.debug = debug
        self.myprint (DEBUG_LEVEL2,     "--> MQTTConn init_ called, ipadr: {}".format(ipadr))    
        self.path = path                 # pfad  where the script is running
        self.mqtt_client_id = client 
        self.mqtt_broker_ip_cmdl = ipadr        # value from commandline (if present)
        self.mqttc = 0                      # Instance of mqtt
        self.broker_ok = False
        self.retry = retry
        self.s = 0
        self.connect_flag = False
        self.mqtt_error = 0
        self.config_filename =  conf   # path and name of config file 
        self.config_section = "mqtt"
        self._IP_extern =""                      # this machines ip adr
        self._IPlocalhost = "127.0.0.1"            # localhost
        self.ipadr_to_use = ""                   # ipad we are going to use
        self.printstring = "--> MQTT_Conn: "
        self.retry_counter = 1
               
               
#   Config Directory containing important parameters
#   will be updated from the configfile
#   here are the defaultvalues in a python directory (key value pair)
        self.cfgdir_mqtt = {
            "mqtt_ipadr"    : "",
            "mqtt_port"     :  "1883",
            "mqtt_keepalive_intervall" : "45",
            "mqtt_userid"   : "myuserid" ,
            "mqtt_pw"       : "mypassword",
            "mqtt_qos"      : 0  ,
            "mqtt_retain"   : 0 ,
            "retry_intervall" : 1,          # seconds
            "retry_counter"  : 2,
            "userdata"      : "u-data",
        }

 # get get data from configfile
        
        if (self.debug > 2):
            print ( self.printstring + "Parameters before read configfile:")
            for x, y in self.cfgdir_mqtt.items():
                print(x, y)
        
        
        config = ConfigRead(debug_level = self.debug)        # instanz der ConfigRead Class
        ret = config.config_read(self.config_filename, self.config_section,self.cfgdir_mqtt)  # alese von abschnitt mqtt
#        ret = 0

        if ret > 0:
            self.myprint (DEBUG_LEVEL3, self.printstring + "MQTT_Conn: config_read has retcode: {}".format (ret))
            self.errorcode = 99
            return None

        self.myprint (DEBUG_LEVEL3,  self.printstring + "mqtt_conn_init_ called, client_id:{}".format(self.mqtt_client_id) )

        if (self.debug > 2):
            print ( self.printstring + "Parameters after read configfile:")
            for x, y in self.cfgdir_mqtt.items():
                print(x, y)

# add random chars to client-id (in case user runs program twice)
        self.mqtt_client_id = self.mqtt_client_id.join(random.choice("ABCDEFG") for _ in range(2))
        


# Eventhandler
#----Function Callback (msg gekommen )--------------------------------
        def __my_on_message__ (client,userdata, msg):         
            self.myprint (DEBUG_LEVEL3,"--> MQTT_Conn: my_on_message() called ")
  
# Eventhandler
#----Function Callback (msg gesendet )--------------------------------
        def __my_on_publish__ (client,userdata,mid):         
            self.myprint (DEBUG_LEVEL3, self.printstring + "my_on_publish() called")
             
# Eventhandler
#------------
        def __my_on_subscribe__ (client, userdata, mid, qos):
            self.myprint (DEBUG_LEVEL3,  self.printstring + "my_on_subscribe() called, userdata: {}".format(userdata) )

# Eventhandler
#------------
        def __my_on_unsubscribe__ (client, userdata, mid):
            self.myprint (DEBUG_LEVEL3,  self.printstring + "my_on_unsubscribe() called, userdata: {}".format(userdata) )

# Eventhandler
#------------
        def __my_on_disconnect__ (client, userdata, rc):
            if rc != 0:
                self.myprint (DEBUG_LEVEL0,  self.printstring + "unexpected disconnection from broker")
            else:
                self.myprint (DEBUG_LEVEL0,  self.printstring + "regular disconnection from broker")            
            self.connect_flag = False
                          
# Eventhandler
#------------
        def __my_on_connect__ (client, userdata, flags, rc):
            self.mqtt_error = 0 
            self.myprint (DEBUG_LEVEL3,  self.printstring + "my_on_connect() called, rc: {}".format(rc) )
            if rc == 0:
                self.myprint (DEBUG_LEVEL3,  self.printstring + "connection OK, rc: {}".format(rc) )
                self.connect_flag = True
            else:
                self.myprint (DEBUG_LEVEL0,  self.printstring + "connection NOTOK, rc: {}".format(rc) )
                if (rc == 5):
                    self.myprint (DEBUG_LEVEL0,  self.printstring + "user_id/password pair not correct")
                self.connect_flag = False
                self.mqtt_error = rc         
        
#---------------    
        
# get this machines IP address, externe iP Adresse
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
                # doesn't even have to be reachable
            self.s.connect(('10.255.255.255', 1))
            self._IP_extern = self.s.getsockname()[0]
        except:         # wenn Fehler
            self._IP_extern = self._IPlocalhost  # "127.0.0.1"
        finally:
            self.s.close()

 #  now determine which ip addr to use: the one from the commandline parm has precendence
 #  if none is given on the commandline check if the one in configfile is > 0
 #  if this is present, take it, if not use 127.0.0.1 
 #     
        # default broker IP        
        self.ipadr_to_use =  self._IPlocalhost
        # set from config if present
        if (len(self.cfgdir_mqtt["mqtt_ipadr"])> 0):
            self.ipadr_to_use =  self.cfgdir_mqtt["mqtt_ipadr"]
        # set from commandline ifpresent
        if (len(self.mqtt_broker_ip_cmdl) > 0):                       # from cammandline
            self.ipadr_to_use = self.mqtt_broker_ip_cmdl               # use this if present      

                  
        self.myprint (DEBUG_LEVEL1,  self.printstring + "Use this IP-Adr:{}".format(self.ipadr_to_use))
        self.myprint (DEBUG_LEVEL1,  self.printstring + "UserID:{}, Passwort:{}, QoS:{} , Retain:{}".format \
        (self.cfgdir_mqtt["mqtt_userid"], self.cfgdir_mqtt["mqtt_pw"], self.cfgdir_mqtt["mqtt_qos"], self.cfgdir_mqtt["mqtt_retain"]))
        self.myprint (DEBUG_LEVEL2,  self.printstring + "retry_intervall:{}  retry_counter:{}".format(self.cfgdir_mqtt["retry_intervall"], self.cfgdir_mqtt["retry_counter"]))

# finally, we come the actual MQTT stuff, we know the ip addr to use
        self.mqttc = mqtt.Client(self.mqtt_client_id, True, self.cfgdir_mqtt["userdata"])       # Initiate MQTT Client

    # Register Event Handlers
        self.mqttc.on_connect   = __my_on_connect__              # setup on connect callback
        self.mqttc.on_subscribe = __my_on_subscribe__          # setup on subscribe callback
        self.mqttc.on_unsubscribe = __my_on_unsubscribe__          # setup on unsubscribe callback
        self.mqttc.on_message   = __my_on_message__
        self.mqttc.on_disconnect = __my_on_disconnect__  
        self.mqttc.on_publish   = __my_on_publish__    
        

# set userid and password            

        self.mqttc.username_pw_set(username = self.cfgdir_mqtt["mqtt_userid"], password = self.cfgdir_mqtt["mqtt_pw"])

 # Connect with MQTT Broker    
 
        self.__connect_broker__()
 
        pass

# ------ init ends here --------------
#-------------------------------------------
# __repr__ function MQTT_Conn
# 
    def __repr__ (self):

        rep = "MQTT_Conn ( )"
        return (rep)   
                

# --- private function connect_broker()
#---------------------------------------------------
    def __connect_broker__ (self):
        pass
        
        self.retry_counter = int(self.cfgdir_mqtt["retry_counter"])
        
        
        while ( self.retry_counter > 0):
            try:
                self.connect_flag = False               # set to False and try connection

            
        
                self.mqttc.connect(self.ipadr_to_use, int(self.cfgdir_mqtt["mqtt_port"]), int(self.cfgdir_mqtt["mqtt_keepalive_intervall"])) 
     #       self.mqttc.connect(self.ipadr_to_use,1883)         # for test
                time.sleep(0.2) 
                self.mqttc.loop_start()                             # start the loop, see docu
        
                time.sleep(0.3)
                if self.connect_flag:
                    self.myprint (DEBUG_LEVEL0,  self.printstring + "MQTT Connect OK")        
                    break        # connect seems ok          
                else:
                    if self.mqtt_error == 5:            # treat error user_id/password differently
                        return (self.mqtt_error)     
            except ConnectionRefusedError:
                self.myprint (DEBUG_LEVEL0,  self.printstring + "connection to broker failed")                                
                pass

            finally:
                pass
            if not self.retry:                          # retry is True if retry requested
                self.retry_counter -= 1                 # if not requested, retry
            self.myprint (DEBUG_LEVEL3,  self.printstring + "doing retry on connection")                    
            time.sleep(int(self.cfgdir_mqtt["retry_intervall"]))
 #           print (self.retry_counter )
            pass     
        
    
        if not self.connect_flag:
            self.myprint (DEBUG_LEVEL0,  self.printstring + "MQTT Connect failed, is the mosquitto running?")
            self.myprint (DEBUG_LEVEL0, self.printstring +  "restart mosquitto with 'sudo service mosquitto restart'") 
            self.mqtt_error=128            
        return (self.mqtt_error)    
               
        
# --- Publish -------------------------------------
# --- with errorhandling if publish fails
    def publish_msg (self,topic, payload):
       # self.myprint (DEBUG_LEVEL2,  self.printstring +   "publish_msg() called, topic:{}, payload:{}".format(topic,payload))
        self.myprint (DEBUG_LEVEL2,  self.printstring +   "publish_msg() called, topic:{}".format(topic))
        pass

        if not self.connect_flag:           # return error 55 if no connection to broker
            self.mqtt_error = 55
            return ( self.mqtt_error )

        # ---- publish a message   
        # we try to catch ValueErrors on publish, this cn happen if the topic string has zero lenght        
        try:
            publish_result = self.mqttc.publish (topic , payload, qos=0, retain=False)
        except ValueError:
            self.myprint (DEBUG_LEVEL0,  self.printstring +   "publish error, check your topic string!")
            self.mqtt_error = 77
            return ( self.mqtt_error )          
        finally:
            pass
        

        # ------------------
        if (publish_result.rc != 0):
            self.myprint (DEBUG_LEVEL3,  self.printstring +   "publish failed errcode:{}".format (publish_result.rc))
        for z in range (PUBLISH_COUNTER):
            if self.connect_flag:
                self.mqtt_error =   0   
                break        # connect seems ok
            else:
                sleep(0.7)
            
        if not self.connect_flag:           # no connection, so discoonect must have happened
            pass
            self.myprint (DEBUG_LEVEL0,  self.printstring + "could not publish, connection broken")
            self.mqtt_error = 8            
 
        time.sleep(0.5)
 #       print (publish_result.is_published())
        pass
        return ( self.mqtt_error )          # returns zero if ok published

#---------------------------------------------------
    def loop_forever(self):
        self.myprint (DEBUG_LEVEL3,  self.printstring + "loop_forever() called")
        self.mqttc.loop_forever()      
        print ("loop_forever() beendet")
        return

    def loop_stop(self):
        self.myprint (DEBUG_LEVEL3,  self.printstring + "loop_stop() called")
        self.mqttc.loop_stop()
        self.mqttc.disconnect() # disconnect
        return

    def loop(self,seconds):
        self.myprint (DEBUG_LEVEL3,  self.printstring + "loop() called")
        mqttc.loop(seconds) #timeout = 2s
        return

#---------------------------------------------------
    def loop_start(self):
        self.myprint (DEBUG_LEVEL3,  self.printstring + "loop_start() called")
        self.mqttc.loop_start()
        return


#---------------------------------------------------
    def get_status(self):
        self.myprint (DEBUG_LEVEL3,  self.printstring + "get_status() called, mqtt_error : {}".format(self.connect_flag))
        return (self.connect_flag, self.mqtt_error)


#---------------------------------------------------
    def reconnect (self):
        self.myprint (DEBUG_LEVEL0,  self.printstring + "reconnect() called")
        self.mqttc.loop_stop()         
        self.connect_flag = False               # set to False and try connection
        try:
            self.mqttc.reconnect() 
            self.mqttc.loop_start() 
            self.myprint (DEBUG_LEVEL0,  self.printstring + "reconnect sucessfull") 
            self.connect_flag = True         
        except:
            self.myprint (DEBUG_LEVEL0,  self.printstring + "reconnect refused")        
        finally:
            pass
        
#------------------------------------------------


#--- Method mqtt_set_topic ----------------------
    def subscribe_topic (self, topic_in, callback_function):
        self.myprint (DEBUG_LEVEL2,  self.printstring + "subscribe_topic() called, topic:{}, callb:{}".format(topic_in,callback_function))    
        try:
            res,mid = self.mqttc.subscribe (topic_in, qos=0)
            self.myprint (DEBUG_LEVEL3,  self.printstring + "subscribe retcode: {}".format(res)) 
            if (res == 0):
                self.mqttc.message_callback_add (topic_in,callback_function )
                self.mqtt_error = 0
        except ValueError:
            self.myprint (DEBUG_LEVEL0,  self.printstring +   "subscribe: check your topic string!")
            self.mqtt_error = 77
        finally:
            return ( self.mqtt_error )       

         
        
 #--- Method mqtt_set_will ----------------------
    def set_will (self, topic_in, will_string):
        self.myprint (DEBUG_LEVEL2,  self.printstring + "set_will() called, topic: {}".format(topic_in))
        self.mqttc.will_set (topic_in, will_string, 1, False )
        pass
  
 #--- Method mqtt_set_topic ----------------------
    def unsubscribe_topic (self, topic_in):
        self.myprint (DEBUG_LEVEL2,  self.printstring + "unsubscribe_topic() called, topic: {}".format(topic_in))
        try:
            res,mid = self.mqttc.unsubscribe (topic_in)
            self.myprint (DEBUG_LEVEL3,  self.printstring + "unsubscribe retcode: {}".format(res))       
            if (res == 0):
                self.mqttc.message_callback_remove (topic_in)
                self.mqtt_error = 0
        except ValueError:
            self.myprint (DEBUG_LEVEL0,  self.printstring +   "unsubscribe: check your topic string!")
            self.mqtt_error = 77       
        finally:
            return ( self.mqtt_error )       

        
  
# Eventhandler       
#----Function Callback (msg gekommen )--------------------------------
    def my_callback_msg(self, mosq, obj, msg):
        
        self.myprint (DEBUG_LEVEL3, self.printstring + "my_callback_msg() called with message: topic:{},  payload:{}".format( msg.topic,msg.payload.decode()))
              
        found = False

        if found == False:
            self.myprint (DEBUG_LEVEL0, self.printstring + "my_callback_msg topic3 nicht in topic_list. topic3:{}, topic-list: {} ".format (topic3, self.topic_list))
                 


#-------------Lösche Instanz ------------------------2-----------------
# close sockets und so
    def __del__(self):

        
        if  self.mqtt_error == 0:   
# Disconnect from MQTT_Broker
    
 #           self.mqttc.loop_stop()
        # Disconnect from MQTT_Broker
            self.mqttc.disconnect()

#
#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("mymqtt.py is not callable on the commandline")
    sys.exit(2)
#  --- End of Code ---------------------------------