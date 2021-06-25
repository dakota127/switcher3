#!/usr/bin/python
# coding: utf-8
# ***********************************************************
#
# from: https://github.com/pradeesi/MQTT_Broker_On_Raspberry_Pi/blob/master/publisher.py
#
#
import paho.mqtt.client as mqtt
import socket, sys
import argparse

# Define Variables
MQTT_BROKER = "192.168.1.131"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC = ""


#----------------------------------------------------------
# get and parse commandline args
def argu():
    global MQTT_TOPIC 

    parser = argparse.ArgumentParser()

    parser.add_argument("-t", help="Topic für Suscribe", default="switcher3", type=str)

    args = parser.parse_args()
#    print (args.d, args.s, args.dein, args.daus, args.dnor, args.dexc, args.dinc)          # initial debug
#    if args.s:
#        print ("s war hier")
    if args.t:
        MQTT_TOPIC=args.t
    
    return(args)
    
#------------------------------------------    
# Define on_connect event Handler
#def on_connect(mosq, obj, rc):
def on_connect(self, mqttc,userdata, rc):
	#Subscribe to a the Topic
	self.subscribe(MQTT_TOPIC, 0)
	print ("Using Topic: {}".format(MQTT_TOPIC))

#-----------------------------------------
# Define on_subscribe event Handler
def on_subscribe(mosq, obj, mid, granted_qos):
    print ("Subscribed to MQTT Topic")

#----------------------------------------
# Define on_message event Handler
def on_message(mosq, obj, msg):
    msg = msg.payload.decode()
    print (msg)


# ---------- Run the stuff ----------------
def runit():

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# eigene IP Adr ermitteln
    try:
    # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
            
#     jetzt ist eigene IP Adr bekannt        
    MQTT_BROKER = IP
    
    print ("Switcher Test MQTT Subscribe, using IP_ADR: {}".format(MQTT_BROKER))
    
    # Initiate MQTT Client
    mqttc = mqtt.Client()
    
    # Register Event Handlers
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe
    
    try:
        mqttc.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL) 
    except:
        print("MQTT Connect failed, is mosquitto broker running?")
        print("start mosquitto mit 'sudo service mosquitto restart'")
        sys.exit(2)
    
    # Continue the network loop
    try:
        mqttc.loop_forever()
        
    except KeyboardInterrupt:
        print ('^C received, shutting down the subscriber')
    
    finally:
    # Disconnect from MQTT_Broker
        mqttc.disconnect()
    #
       
            
# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    options=argu()        
 
    runit()
         
             
