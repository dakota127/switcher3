#!/usr/bin/python
# coding: utf-8
# ***********************************************************
#
# from: https://github.com/pradeesi/MQTT_Broker_On_Raspberry_Pi/blob/master/publisher.py
#
#
# Import package
import paho.mqtt.client as mqtt
import socket
import sys
import argparse

# Define Variables
MQTT_BROKER = "192.168.1.131"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC = ""
MQTT_MSG = "Hello MQTT from testpublisher"

#----------------------------------------------------------
# get and parse commandline args
def argu():
    global MQTT_TOPIC , MQTT_MSG 

    parser = argparse.ArgumentParser()

    parser.add_argument("-t", help="Topic für Publisch", default="switcher3", type=str)
    parser.add_argument("-p", help="Payload für Publish", default="abc", type=str)
    args = parser.parse_args()
#    print (args.d, args.s, args.dein, args.daus, args.dnor, args.dexc, args.dinc)          # initial debug
#    if args.s:
#        print ("s war hier")
    if args.t:
        MQTT_TOPIC=args.t
    if args.p:
        MQTT_MSG=args.p
   
    return(args)
    
#------------------------------------------    
# Define on_connect event Handler
def on_connect(mosq, obj, rc):
	print ("Connected to MQTT Broker")

#-----------------------------------------
# Define on_publish event Handler
def on_publish(client, userdata, mid):
	print ("Message Published...")

# ---------- Run the stuff ----------------
def runit():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
    # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
            
            
    MQTT_BROKER = IP
    print ("Switcher Test MQTT Publisher, using IP_ADR: {} and Port: {}".format(MQTT_BROKER,MQTT_PORT))
    # Initiate MQTT Client
    
    mqttc = mqtt.Client()
    # Register Event Handlers
    mqttc.on_publish = on_publish
    mqttc.on_connect = on_connect
    
    
    # Connect with MQTT Broker
    try:
        mqttc.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL) 
    except:
        print("MQTT Connect failed, is mosquitto broker running?")
        print("start mosquitto mit 'sudo service mosquitto restart'")
        sys.exit(2)
        
    # Publish message to MQTT Topic 
    print("Publish Topic: {}".format(MQTT_TOPIC))
    print("Publish Payload: {}".format(MQTT_MSG))
    mqttc.publish(MQTT_TOPIC,MQTT_MSG)
    
    # Disconnect from MQTT_Broker
    mqttc.disconnect()
    
    

# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    options=argu()        
 
    runit()



