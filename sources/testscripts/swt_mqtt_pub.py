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
MQTT_BROKER_IPADR = "127.0.0.1"         # default value, durch commandline parm zu ändern
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC = ""
MQTT_MSG = "Hello MQTT from testpublisher"
mqtt_broker_ip_cmdline = ""
broker_user_id = ""
broker_user_passwort = ""

#----------------------------------------------------------
# get and parse commandline args
def argu():
    global MQTT_TOPIC , MQTT_MSG ,mqtt_broker_ip_cmdline, broker_user_id, broker_user_passwort

    parser = argparse.ArgumentParser()

    parser.add_argument("-t", help="Topic für Publish", default="test", type=str)
    parser.add_argument("-d", help="Payload für Publish", default="Hello from testpublisher", type=str)
    parser.add_argument("-i", help="IP Addr" , type=str)
    parser.add_argument("-u", help="User-Id",  default="test127", type=str)
    parser.add_argument("-p", help="Passwort", default="123-123", type=str)
    args = parser.parse_args()
#    print (args.d, args.s, args.dein, args.daus, args.dnor, args.dexc, args.dinc)          # initial debug
#    if args.s:
#        print ("s war hier")
    if args.t:
        MQTT_TOPIC=args.t
    if args.p:
        MQTT_MSG=args.d
    if args.i: 
        mqtt_broker_ip_cmdline = args.i
   
    if args.u: 
        broker_user_id = args.u
    if args.p: 
        broker_user_passwort = args.p
    return(args)
    
#------------------------------------------    
# Define on_connect event Handler
def on_connect(self, mqttc,userdata, rc):
    print ("on_connect called, rc:{}".format(rc))

#-----------------------------------------
# Define on_publish event Handler
def on_publish(client, userdata, mid):
	print ("Message Published...")

# ---------- Run the stuff ----------------
def runit():
    global MQTT_BROKER_IPADR, mqtt_broker_ip_cmdline, broker_user_id, broker_user_passwort

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
    # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IPAdr_this_machine = s.getsockname()[0]
    except:
        IPAdr_this_machine = '127.0.0.1'
    finally:
        s.close()
        print("IPAdr this machine:{}".format(IPAdr_this_machine))


    # falls eine Ipadr auf der commandline gegeben wird, nehme diese
    if len (mqtt_broker_ip_cmdline) >0 :

        MQTT_BROKER_IPADR = mqtt_broker_ip_cmdline
        

    print ("Switcher Test MQTT Publisher, using IP_ADR:{} and Port:{}".format(MQTT_BROKER_IPADR, MQTT_PORT))
    
    
    # Initiate MQTT Client
    mqttc = mqtt.Client()
    # Register Event Handlers
    mqttc.on_publish = on_publish
    mqttc.on_connect = on_connect
    
    # set userid and password            
    mqttc.username_pw_set(username = broker_user_id, password = broker_user_passwort)
    
    print ("Using User_id:{} and Password:{}".format(broker_user_id, broker_user_passwort))
    # Connect with MQTT Broker
    try:
        mqttc.connect(MQTT_BROKER_IPADR, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL) 
    except:
        print("MQTT Connect failed, is mosquitto broker running?")
        print("start mosquitto mit 'sudo service mosquitto restart'")
        sys.exit(2)
    finally:
        pass

    # Publish message to MQTT Topic 
    print("About to Publish Topic:{} and Payload:{}".format(MQTT_TOPIC,MQTT_MSG))
    mqttc.publish(MQTT_TOPIC, MQTT_MSG)
    
    # Disconnect from MQTT_Broker
    mqttc.disconnect()
    
    

# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#
    options=argu()        
 
    runit()



