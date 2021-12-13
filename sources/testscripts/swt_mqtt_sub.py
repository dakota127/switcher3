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
MQTT_BROKER_IPADR = "127.0.0.1"         # default value, durch commandline parm zu ändern
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 45
MQTT_TOPIC = ""
mqtt_broker_ip_cmdline = ""
broker_user_passwort = ""
broker_user_id = ""

#----------------------------------------------------------
# get and parse commandline args
def argu():
    global MQTT_TOPIC , mqtt_broker_ip_cmdline, broker_user_id, broker_user_passwort

    parser = argparse.ArgumentParser()

    parser.add_argument("-t", help="Topic für Subscribe", default="test", type=str)
    parser.add_argument("-i", help="IP Addr", type=str)
    parser.add_argument("-u", help="User-Id",  default="test127", type=str)
    parser.add_argument("-p", help="Passwort", default="123-123", type=str)
    args = parser.parse_args()
#    print (args.d, args.s, args.dein, args.daus, args.dnor, args.dexc, args.dinc)          # initial debug
#    if args.s:
#        print ("s war hier")
    if args.t:
        MQTT_TOPIC=args.t
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
	#Subscribe to a the Topic
    print ("on_connect called, rc:{}".format(rc))
    if rc > 0:
        print ("Connect failed, quit")
        sys.exit(2)
    try:
        print ("Subscribe using Topic:{}".format(MQTT_TOPIC))
        self.subscribe(MQTT_TOPIC, 0)
    except:
        print ("Subscribe failed")

    finally:
        pass
#-----------------------------------------
# Define on_subscribe event Handler
def on_subscribe(mosq, obj, mid, granted_qos):
    print ("Subscribed to MQTT Topic")

#----------------------------------------
# Define on_message event Handler
def on_message(mosq, obj, msg):
    payload = msg.payload.decode()

    print ("Message received with topic:{} and payload:{}".format(msg.topic, payload))


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
        

    print ("Switcher Test MQTT Subscriber, using IP_ADR:{} and Port:{}".format(MQTT_BROKER_IPADR, MQTT_PORT))
    
    
    # Initiate MQTT Client
    mqttc = mqtt.Client()
    
    # Register Event Handlers
    mqttc.on_message = on_message
    mqttc.on_connect = on_connect
    mqttc.on_subscribe = on_subscribe
    
    # set userid and password            
    mqttc.username_pw_set(username = broker_user_id, password = broker_user_passwort)
    
    print ("Using User_id:{} and Password:{}".format(broker_user_id, broker_user_passwort))
    try:
        print ("About to connect to:{}".format(MQTT_BROKER_IPADR))
        mqttc.connect(MQTT_BROKER_IPADR, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL) 
    except:
        print("MQTT Connect failed, is mosquitto broker running?")
        print("start mosquitto mit 'sudo service mosquitto restart'")
        sys.exit(2)
    finally:
        pass

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
    options = argu()        
 
    runit()
         
             
