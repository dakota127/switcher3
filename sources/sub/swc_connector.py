#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class SwConnector 
#   
#   Diese Class kapselt die Kommunikation zwischen zwei Endpoints
#   Hier also switcher3 und swserver3
#   Switcher hat Endpoint 1
#   Swserver hat Endpoint 2
#
#   diese Class erbt von der MyPrint Class
#   diese Class benutzt die MQtt Class (only if needed)
#   
#   Feb 2021 
#************************************************
#
import os
import sys
import time
from time import sleep
from datetime import date, datetime, timedelta
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output
from sub.myconfig import ConfigRead
import json
 
DEBUG_LEVEL0=0                      
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3

# messages to frontend
TOFE_DONEDEV    = 1
TOFE_DONESWITCH = 2
TOFE_RESET_ALL  = 9

# message from Frontend
FROMFE_DEVTOG   = 1
FROMFE_DEVTAUTO = 2
FROMFE_SWITOG   = 3
FROMFE_ALLAUTO  = 4
FROMFE_ALLOFF   = 5
FROMFE_ALLON   = 6
FROMFE_STAT     = 7


MQTT_TOPIC_SERVPUB      =     "swi/as"          # In Switcher:  SUBSCRIBE receiving from server
                                                # In Server:    PUBLISH sending to switcher

MQTT_TOPIC_SERVPUB_SY   =     "swi/snyc"        # In Switcher:  SUB receiving froms server
                                                # In Server :   PUB sending to Switcher

MQTT_TOPIC_SWIPUB       =     "serv/as"         # In Switcher:  PUB sending to server
                                                # In Server:    SUB receiving from switcher


MQTT_TOPIC_SUBSWIT =   "toswitcher"         # SUB receiving at switcher from flask server
MQTT_TOPIC_RESP =   "response"           # PUB sending to flask server
progname = "swc_connector "

MSG_ASYNC = 0
MSG_SYNC  = 1


receive_window = False
synch_msg_in = ""
message_received_flag = False


#----------------------------------------------------
# Class Definition SWInterface, erbt vom MyPrint
#----------------------------------------------------
class SwConnector (MyPrint):
    ' klasse SwConnector '
    
    send_message_number = 0 
    
    def __init__(self, debug, path, configfile, endpoint, mqtt_client, callback):  # Init Funktion
        self.errorcode = 8
        self.debug = debug
        self.endpoint = endpoint    # 1= switcherside 2= serverside
        self.mqttc = mqtt_client  
        self.callback = callback  
        self.configfile = configfile
        self.path = path 
        self.payload = ""     
        self.payl = "" 
        self.mqtt_error = 0
        self.data = ""
        self.mqtt_connect = False
        self.mqtt_error = 0
       

        self.myprint (DEBUG_LEVEL1, "\t\t" + progname + " _init called, endpoint: {}".format(self.endpoint))
#      config=ConfigRead(self.debug)        # instanz der ConfigRead Class

        if ( self.mqttc == None ):              # we need to establish mqtt connection
            self.myprint (DEBUG_LEVEL2, "\t\t" + progname + " mqtt setup needed ")
            from sub.mymqtt import MQTT_Conn              # Class MQTT_Conn handles MQTT stuff
            #-----------------------------------
            # create Instance of MQTT-Conn Class  
            self.mqttc = MQTT_Conn ( debug = self.debug, 
                        path = self.path, 
                        client = "connector", 
                        ipadr = "", 
                        retry = False, 
                        conf = path + "/" + self.configfile)    # creat instance, of Class MQTT_Conn     

        else:
            self.myprint (DEBUG_LEVEL2, "\t\t" + progname +  " mqtt setup already supplied ")
        

#  Check connection status mqtt
        self.mqtt_connect, self.mqtt_error = self.mqttc.get_status()           # get connection status
    #  returns mqtt_error = 128 if not connected to broker
        if self.mqtt_connect == True:
            self.myprint (DEBUG_LEVEL0, "\t\t" + progname + " connected to mqtt broker")
         # subscribe to MQTT topics   
            self.do_subscribe()                           # doing subscribe
        else:
            self.myprint (DEBUG_LEVEL0, "\t\t" + progname + " did NOT connect to mqtt broker, error: {}".format(self.mqtt_error))       
        # we are quitting if no connection
        
        self.errorcode = 0    # init aktor ok


#-------------------------------------------
# __repr__ function class SwConnector
# 
    def __repr__ (self):

        rep = "SwConnector (Endpoint:" +  str(self.endpoint)  + ")"
        return (rep)

#-------------------------------------------
#  status function class SwConnector
# 
    def mqtt_status (self):
        self.myprint (DEBUG_LEVEL1, "\t\t" + progname + " mqtt_status called")
        return (self.mqttc.get_status())


#---------------------------------------------------------------       
# --- etrminate mqtt loop
# --- needs to be called after initial connection and after reconnect
#-------------------------------------------------------------       
    def terminate (self):
        self.myprint (DEBUG_LEVEL3, "\t\t" + progname + " terminate called ")
        self.mqttc.loop_stop()


#---------------------------------------------------------------       
# --- do subscribe to messages 
#       swserver side is using endpoint 2
#       switcher side ist using endpoint 1
#
# --- needs to be called after initial connection and after reconnect
#-------------------------------------------------------------       
    def do_subscribe(self):

        self.myprint (DEBUG_LEVEL1,  "\t\t" + progname + " do_subscribe called, endpoint:{}".format(self.endpoint)) 
        # endpoint 1 is switcher program
        #   
        if (self.endpoint == 1):    
            # switcher subscribes to 2 topics:
            # subcribe to topic swi/as (async Message sent from server to switcher)            
            res = self.mqttc.subscribe_topic (MQTT_TOPIC_SERVPUB , self.handle_incoming_asyncmsg)     # subscribe to async messages
            if (res > 0):
                self.myprint (DEBUG_LEVEL0,  "\t\t" + progname + " subscribe async returns errorcode: {}".format(res)) 
                self.myprint (DEBUG_LEVEL0,  "\t\t" + progname + " terminating")       
                sys.exit(2)                     # cannot proceed

            # subcribe to topic swi/sync (sync Message sent from server to switcher)  
            res = self.mqttc.subscribe_topic (MQTT_TOPIC_SERVPUB_SY , self.handle_incoming_syncmsg)     # subscribe to 'sync messages'
            if (res > 0):
                self.myprint (DEBUG_LEVEL0,  "\t\t" + progname + " subscribe sync returns errorcode: {}".format(res)) 
                self.myprint (DEBUG_LEVEL0,  "\t\t" + progname + " terminating")       
                sys.exit(2)                     # cannot proceed

            return

        # endpoint2 ist swserver program, subscribe to topic serv/as
        else:   
            # server subscribes to one topic only
            # subcribe to topic serv/as (async Message sent from switcher to server)           
            res = self.mqttc.subscribe_topic (MQTT_TOPIC_SWIPUB , self.handle_incoming_asyncmsg)     # subscribe to topic
            if (res > 0):
                self.myprint (DEBUG_LEVEL0,  "\t\t" + progname + " subscribe async returns errorcode: {}".format(res)) 
                self.myprint (DEBUG_LEVEL0,  "\t\t" + progname + " terminating")       
                sys.exit(2)     
            return

#---------------------------------------------------------------       
# --- do unsubscribe to messages 
#       swserver side is using endpoint 2
#       switcher side ist using endpoint 1
#
# --- needs to be called when unsubscribe is needed
#-------------------------------------------------------------       
    def do_unsubscribe(self):


        self.myprint (DEBUG_LEVEL1,  "\t\t" + progname + " do_unsubscribe called, endpoint:{}".format(self.endpoint)) 
        # endpoint 1 is switcher program
        #   
        if (self.endpoint == 1):    
            # switcher subscribes to 2 topics:
            # subcribe to topic swi/as (async Message sent from server to switcher)            
            res = self.mqttc.unsubscribe_topic (MQTT_TOPIC_SERVPUB)     # unsubscribe
            if (res > 0):
                self.myprint (DEBUG_LEVEL0,  "\t\t" + progname + " unsubscribe async returns errorcode: {}".format(res)) 


            # subcribe to topic swi/sync (sync Message sent from server to switcher)  
            res = self.mqttc.unsubscribe_topic (MQTT_TOPIC_SERVPUB_SY)     # unsubscribe to 'sync messages'
            if (res > 0):
                self.myprint (DEBUG_LEVEL0,  "\t\t" + progname + " unsubscribe sync returns errorcode: {}".format(res)) 
    
            return

        # endpoint2 ist swserver program, subscribe to topic serv/as
        else:   
            # server subscribes to one topic only
            # subcribe to topic serv/as (async Message sent from switcher to server)           
            res = self.mqttc.unsubscribe_topic (MQTT_TOPIC_SWIPUB)     # unsubscribe to topic
            if (res > 0):
                self.myprint (DEBUG_LEVEL0,  "\t\t" + progname + " unsubscribe async returns errorcode: {}".format(res)) 
            return

#---------------------------------------------------------------        
# handle incoming messages (FROM webserver) with MQTT_TOPIC_SUBSWIT
#---------------------------------------------------------------
    def handle_incoming_asyncmsg (self, client,userdata, message):
        global what_to_do, terminate

     #   if (self.endpoint != 1):
     #       self.myprint (DEBUG_LEVEL0, " swconnector wrong endpoint !: ")
     #       return  

        self.myprint (DEBUG_LEVEL2, "\t\t" + progname + " handle_incoming_asyncmsg, endpoint:{}". format(self.endpoint))
        self.data = message.payload.decode()
        try:
            self.data = json.loads(self.data)   # JSON Object wird in Python List of List gewandeltmessage.payload.decode()
            self.myprint (DEBUG_LEVEL2, "\t\t" + progname + " handle_incoming_asyncmsg2:{}". format(self.data))
        except:
            print ("Json error")
            self.data = [self.data,0,0,0]    # error only

        # callback is set at creation of object (it points to a function in switcher if endpoint is 1)
        #                                       (or to a function in swserver if endpoint is 2)
        self.callback (MSG_ASYNC , self.data)   # goes to notifySwitcher or notifyServer (either switcher3 or swserver3 )
        return

#---------------------------------------------------------------        
# handle incoming messages (FROM webserver) with MQTT_TOPIC_SERVPUB_SY (so called sync messages)
#   THIS IS USED on endpoint 1 (Switcher side)
#---------------------------------------------------------------
    def handle_incoming_syncmsg (self, client,userdata, message):
        global what_to_do, terminate


        self.myprint (DEBUG_LEVEL2, "\t\t" + progname + " handle_incoming_syncmsg:{}". format(message.payload.decode()))
        self.data = message.payload.decode()
        try:
         #   self.data = json.loads(self.data)   # JSON Object wird in Python List of List gewandeltmessage.payload.decode()
            self.myprint (DEBUG_LEVEL2, "\t\t" + progname + " handle_incoming_syncmsg2:{}". format(self.data))
        except:
            self.myprint (DEBUG_LEVEL0, "\t\t" + progname + "Json error in handle_incoming_syncmsg()")

        self.callback (MSG_SYNC , self.data)               # goes to notifySwitcher 
        return


#---------------------------------------------------------------        
# handle incoming sync messages (FROM switcher)  (these carry the response topic)
# THIS IS USED on endpoint 2  (server side)
#---------------------------------------------------------------
    def handle_incoming_syncmsg_2 (self, client, userdata, msg):

        global receive_window, synch_msg_in, message_received_flag

        message_received_flag = False
        self.myprint (DEBUG_LEVEL2, "\t\t" + progname  + "handle_incoming_syncmsg_2 () called - topic: {},  payload: {}".format( msg.topic,msg.payload.decode()))
       
        msg = msg.payload.decode()  
        msg_numbr = int(msg[:4])

        self.myprint (DEBUG_LEVEL2, "\t\t" + progname  + "i have msg_number:{}".format(SwConnector.send_message_number))
        self.myprint (DEBUG_LEVEL2, "\t\t" + progname  + "es kommt msg_number:{}".format(msg_numbr))
    

        if SwConnector.send_message_number != (msg_numbr):
          #  self.myprint (DEBUG_LEVEL1, "\t\t" + progname + "message wrong number: {0:0>4}/{0:0>4}".format(SwConnector.send_message_number, msg_numbr)   )
            self.myprint (DEBUG_LEVEL1, "\t\t" + progname + "message wrong number: {}/{}".format(SwConnector.send_message_number, msg_numbr)   )
            return                                  # msg consumed, but worthless 

        if receive_window == False:
            self.myprint (DEBUG_LEVEL1, "\t\t" + progname + "message outside receive_window, payload: {}".format(msg)   )
            return                                  # msg consumed, but worthless 
        
        message_received_flag = True

        synch_msg_in =  msg[4:]                     # move the message
        


#------------------------------------------------
#   init for request_response, only used by the client (eg swserver), endpoint == 2
#-----------------------------------------------
    def request_response_init(self, response_topic):
        self.myprint (DEBUG_LEVEL2, "\t\t" + progname  + "Req_response_init() called, topic:{}".format(response_topic))

        if (self.endpoint != 2):
            self.myprint (DEBUG_LEVEL0, " swconnector wrong endpoint !: ")
            return

        res = self.mqttc.subscribe_topic (response_topic , self.handle_incoming_syncmsg_2)     # subscribe to topic
        

#---------------------------------------------------------------------
# function switcher_send (send message to webserver) (mqtt topic MQTT_TOPIC_PUBSERV)
# message must be string (caller must do xy = json.dumps() if necessary)
#------------------------------------------------------------------------
    def transmit (self, message, topic = "def"):


        self.myprint (DEBUG_LEVEL2, "\t\t" + progname + " transmit() called, topic:{}, msg:{}".format(topic,message))  

       
        if (self.endpoint == 1):                # endpoint is switcher3
            if topic == "def":
                topic = MQTT_TOPIC_SWIPUB
            self.mqtt_error = self.mqttc.publish_msg (topic, message)
            if (self.mqtt_error > 0):
                self.myprint (DEBUG_LEVEL1,  "\t\t" + progname + " publish returns: {} ".format(self.mqtt_error))
            return (self.mqtt_error)

        elif (self.endpoint == 2):              # endpoint 2 ist swserver
            if topic == "def":
                topic = MQTT_TOPIC_SERVPUB
            self.mqtt_error = self.mqttc.publish_msg (topic, message)
            if (self.mqtt_error > 0):
                self.myprint (DEBUG_LEVEL1,  "\t\t" + progname + " publish returns: {} ".format(self.mqtt_error))
            return (self.mqtt_error)
        else:
            self.myprint (DEBUG_LEVEL0, "\t\t" + progname +  " wrong endpoint !: ")
            return (9)  
        

        return (0)


##---------------------------------------------------------------------
# function transmit_sync (send message to webserver, using response topic) 
#------------------------------------------------------------------------
    def transmit_sync (self, payload, time_out):
        global receive_window, synch_msg_in, message_received_flag

        SwConnector.send_message_number = SwConnector.send_message_number + 1

        self.myprint (DEBUG_LEVEL2,  "\t\t" + progname + "transmit_sync() called, msg:{}, time_out: {}, number:{}".format(payload, time_out, SwConnector.send_message_number))
    
       # return (3,"  ")                             # <<------------------------

        
        if SwConnector.send_message_number > 998:
            SwConnector.send_message_number = 1
        nbr_str = "{0:0>4}".format(SwConnector.send_message_number)
    
        # assemble message:  counter + resonse_topic + user_message
        suffix = nbr_str + "{:15}".format( MQTT_TOPIC_RESP) 

        payl = suffix + payload         # send this to switcher
       

        receive_window = True
        message_received_flag = False
        self.timeout_flag = False

        #  call transmit -------------------
        self.transmit (message = payl,
                      topic = MQTT_TOPIC_SERVPUB_SY)
        
        start_time = datetime.now()                 # time msg sent
        data1 =""
        while True :
            if message_received_flag:
                break
            time.sleep(0.1)         #wait for message
            self.myprint (DEBUG_LEVEL2,  "\t\t" + progname + "waitung for synch msg...")
            elapsed1 = datetime.now() - start_time
            elapsed1 = (int(elapsed1.total_seconds() * 1000) ) # in ms
            self.myprint (DEBUG_LEVEL3,  "\t\t" + progname +  "Laufzeit (s): {}".format(elapsed1 )  ) 
            if elapsed1 > time_out:
                self.timeout_flag = True
                break
        receive_window == False

        if self.timeout_flag:
            self.myprint (DEBUG_LEVEL2,  "\t\t" + progname + "time_out on synch msg...")
            return (9,"","")
        
        if message_received_flag:

            self.myprint (DEBUG_LEVEL2,  "\t\t" + progname +  "synch response received: {}".format(synch_msg_in))
            request = synch_msg_in[:10]         # strip off request string

            try:
                # ab pos 10 we have a python list
                data1 = json.loads(synch_msg_in[10:])   # JSON Object wird in Python List of List gewandeltmessage.payload.decode()
            #    self.myprint (DEBUG_LEVEL1, "\t\t" + progname + " callback_msg_async_223:{}". format(data1))
            except:
                self.myprint (DEBUG_LEVEL0, "\t\t" + progname + "Json error in transmit_sync()")
               

            return (0,request, data1)             # return request and message
        else: 
            return(8,"","")

##---------------------------------------------------------------------
# function reconnect
#------------------------------------------------------------------------
    def reconnect(self):
        self.myprint (DEBUG_LEVEL1,  "\t\t" + progname +  "reconnect called")
        self.mqttc.reconnect()


#------------- ---------------------------------------
# Terminate SwConnector PArt
#------------------------------------------------------------------------
    def __del__(self):
    #    self.myprint (DEBUG_LEVEL2, "\t\t" + progname + " del called")
        pass   



   
# ************************************************** 		


#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("swc_connector.py ist nicht aufrufbar auf commandline")
    sys.exit(2)

#  end of code -----------------------

    
