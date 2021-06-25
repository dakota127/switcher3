#!/usr/bin/env python
# coding: utf-8
#
#------------------------------
# Beispiel für eigene Thread Class
# wird so im Switcher3 für den Sequencer und für das Blinken verwendet
#
# from
# http://benno.id.au/blog/2012/10/06/python-thread-exceptions
#
#   Mai 2021 PBX
#----------------------------------------------------
from datetime import date, datetime, timedelta

import threading
import time, os, sys
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output

import RPi.GPIO as GPIO                         #  Raspberry GPIO Pins


progname = "thread_6: "
logfile_name = "thread.log"
myprint = None
my_blink = None
debug = 1
path = ""
ALIVE_INTERVALL = 6          # sec between alive log entry (TESTMODE)
DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3


# define Python user-defined exceptions
class Error(Exception):
    """Base class for other exceptions"""
    pass


class ThreadError(Error):
    """Raised when the input value is too small"""
    pass

#-------------------------------------------------
class myBlink(threading.Thread, MyPrint):
  
    def __init__ (self, gpio_blink):
        super().__init__()
        self.myprint (0, "myBlink _init called")
        self.pin = gpio_blink

    def run(self):
        while True:
            for i in range(2):
                GPIO.output(self.pin, True)
                time.sleep(0.1)
                GPIO.output(self.pin, False)
                time.sleep(0.1)
            for i in range(4):
                time.sleep(1)     


# ***** Class blink-led **************************
def blink_led(blink_pin):  # blink led 3 mal und warten  --> in eigenem Thread !!
    global GPIO

    while True:
        for i in range(2):
            GPIO.output(blink_pin, True)
            time.sleep(0.1)
            GPIO.output(blink_pin, False)
            time.sleep(0.1)
        for i in range(4):
            if term_verlangt==1: 
                mypri.myprint (DEBUG_LEVEL1,  progname + "Thread blink_led beendet")	# fuer log und debug
                return
            time.sleep(1)   


#-------------------------------------------------
class myThread(threading.Thread, MyPrint):
    """MyThread should always e used in preference to threading.Thread. """
 #   def __init__(self, *kwarg,**kwargs):
 #       super().__init__(*kwarg,**kwargs)
  
    def __init__ (self, debug_in, path_in, conf):
        super().__init__()
        self.myprint (0, progname + "_init called")
        self.count = 0
        self.debug = debug_in
        self.path = path_in
        self.conf = conf
        self.myprint (0, progname + "_init done")

    def run(self):
        self.myprint (0, progname + "Thread now runs")
        try:
        #
            while self.count < 15:
                self.count +=1

                self.myprint (0, progname + "thread running, count:{}".format(self.count))
                time.sleep(1)
            a = b
            self._real_run()
        except:
            self.myprint_exc ('Exception in Thread.run')
            
        finally:
            print ("thread finally reached")
    
    #-------------------------------------------
    # __repr__ function 
    # 
    def __repr__ (self):

        rep = "MyThread Peter "
        return (rep)

#-------------------------------------------------
def count():
    count_thread = threading.active_count()
    thread_list = threading.enumerate()
        
    myprint.myprint (DEBUG_LEVEL0,"Anzahl Threads: {},  List: {}".format(count_thread,thread_list))
        
#-----------------------------------------------------------------
def main():
    global myprint
    path = os.path.dirname(os.path.realpath(__file__))    # pfad wo dieses script läuft
# create Instance of MyPrint Class 
    
     #Use BCM GPIO refernece instead of Pin numbers
    GPIO.setmode (GPIO.BCM)
    rev = GPIO.RPI_REVISION
    GPIO.setwarnings(False)           
    GPIO.setup(5, GPIO.OUT)
    


    myprint = MyPrint(  appname = progname, 
                    debug_level = debug,
                    logfile =  path + "/" + logfile_name ) 
    # Create new threads

    my_blink = myBlink(5)
    my_blink.setDaemon (True)      
    my_blink.start ()      
    thread1 = myThread(   debug_in = debug, 
                          path_in = "path",
                          conf = "conf"
                        )
                      #       
    print ("object created:{}".format(thread1))
    thread1.daemon = True  # Don't let this thread block exiting.
    thread1.start()

    time.sleep(1)
    count()

    time_old = datetime.now()                           # fuer Zeitmessung
    # setup posit --------------
    try:
       
        myprint.myprint (DEBUG_LEVEL1 ,"Start of Main loop")
        while True:
    #  ---- MAIN LOOP of program ---------------------------------
            time.sleep(.5)
            if thread1.isAlive():
                pass
            else:
                myprint.myprint (DEBUG_LEVEL0 ,"OH SHIT, thread is dead")
                raise ThreadError
            time_new =  datetime.now() 
            delta = time_new - time_old
            delta = int(delta.days * 24 * 3600 + delta.seconds)     # delta in sekunde       
            if delta > ALIVE_INTERVALL:              #   Zeit vorbei ?
                time_old = datetime.now()
                myprint.myprint (DEBUG_LEVEL0 ,"bin am leben..")
                count()
    except KeyboardInterrupt:   
    # aufraeumem
        myprint.myprint (DEBUG_LEVEL0 ,"ohh, Keyboard Interrupt")
    
    except ThreadError:   
    # aufraeumem
        myprint.myprint (DEBUG_LEVEL0 ,"Thread Error raised, wir müssen aufören")
      

    except Exception:
        #       etwas schlimmes ist passiert, wir loggen dies mit Methode myprint_exc der MyPrint Klasse
        myprint.myprint_exc ("etwas Schlimmes ist passiert.... !")
       
    finally: 
    # hierher kommen wir immer, ob Keyboard Exception oder andere Exception oder keine Exception
        time.sleep(1)

        myprint.myprint (DEBUG_LEVEL0 ,"finally reached")	# wir starten       juni2018
       # return(error)

    #    swi_terminate (1)
        sys.exit(0)


#-------------------------------------------------------
# Driver code
if __name__ == '__main__':
    main()
  
	
