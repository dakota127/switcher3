#!/usr/bin/python
# coding: utf-8
# ***********************************************************
# 	Programm zum Testen des TestAufbaus
# 
#   Alle Led's werden eingeschaltet auf Tastendruck
#   
#-------------------------------------------------
#
import RPi.GPIO as GPIO         #  Raspberry GPIO Pins
import sys
from time import sleep
from datetime import date, datetime, timedelta

homebutton = 13
ledon = False

pins = [5,6,24,12,19,20,21]         # led-pins  für switcher testbett mit 5 led ( = dosen)


#---- Callback, wird aufgerufen, wenn Zuhause Pushbutton gedrückt wird
def my_callback_zuhause(channel):
    global ledon
    

    print ("Taste gedrueckt")    
   
    sleep(0.1)  # confirm the movement by waiting 1 sec 
    if not GPIO.input(homebutton): # and check again the input
        pass
        ledon = ledon ^ 1       # toggle ledon
    
    return()


#---------- setup/cleanup GPIO  how= 1 setup
def gpio_setup(how):

    if how:
           #Use BCM GPIO refernece instead of Pin numbers
        GPIO.setmode (GPIO.BCM)
        rev=GPIO.RPI_REVISION
        GPIO.setwarnings(False)            

        GPIO.setup(homebutton, GPIO.IN, pull_up_down=GPIO.PUD_UP)         # pushbutton zuhause
        GPIO.add_event_detect(homebutton, GPIO.FALLING, callback=my_callback_zuhause, bouncetime=300)
    
 
        for led in pins:
            GPIO.setup (led, GPIO.OUT)   # Pin als Output
    else:
        for led in pins:
            GPIO.cleanup(led)
        GPIO.cleanup(homebutton)
 #----------------------------  
def int_str():
    print ("test int to string und umgekehrt")
    int_arr = [0 for z in range(10)]

    int_arr = [1,2,3,4,5,6]
    int_arr[5] = 8
    convert_first_to_generator = (str(w) for w in int_arr)
    stri = ''.join(convert_first_to_generator)  
    print (stri)    
    
    b = [int(i) for i in str(stri)]
    print (b)
    print ("ENDE test int to string und umgekehrt")
    
#--------------------------------------------------
def led_ein():
    global ledon
    
    for led in pins:
        GPIO.output(led, True)     # led on
        sleep (0.1)
        GPIO.output(led, False)     # led on
        sleep(0.1)
   
    for led in pins:
        GPIO.output(led, True)     # led on

    sleep(1.5)
    
    for led in pins:
        GPIO.output(led, False)     # led on
        
    ledon = ledon ^ 1       # toggle ledon
    
                
#--------------------------------------------------    
def runit():

    try:
        while True:
            if ledon:
                print ("Led einschalten ")
                led_ein()
                
            else:
                sleep(0.3)
#                print ("warte auf Taste... ")
    except KeyboardInterrupt:
   
           print ("Keyboard Interrupt, clean up pins")  # aufräumem

    except Exception:
        #       etwas schlimmes ist passiert
            print ("Etwas Schlimmes ist passiert.... !")
    
    finally:
        print ("finally reached...")
        gpio_setup(0)  # clean up GPIO
    
    sys.exit(0)
    

# *************************************************
# Program starts here
# *************************************************

if __name__ == '__main__':
#

    int_str()
    gpio_setup(1)  # set GPIO Pins zum Senden  juni2018  renamed
    print ("druecke zuhause drucktaste...")
    runit()
    
 #---------------------------------------------
 #
    