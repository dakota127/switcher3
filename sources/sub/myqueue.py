#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class Queue 
#   
#   
#   Februar 2021
#************************************************
#
import os
import sys
import time
from time import sleep
from sub.myprint import MyPrint              # Class MyPrint zum printern, debug output

from datetime import date, datetime, timedelta
import threading

DEBUG_LEVEL0=0                      
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3



#----------------------------------------------------
# Class Definition Wetter, erbt vom MyPrint
#----------------------------------------------------
class MyQueue (MyPrint):
    ' klasse queueu '
   
    def __init__(self):
        self._items = []
        self.lock = threading.Lock()

    def enqueue(self, item):
        with self.lock:
            self._items.append(item)

    def dequeue(self):
        with self.lock:
            try:
                return self._items.pop(0)
            except IndexError:
                print("Empty queue")

    def len(self):
        with self.lock:
            return len(self._items)


    def __repr__(self):
        with self.lock:
            return f"Queue({self._items})"     

 # 

#-------------Terminate Action PArt ---------------------------------------
# cleanups
#------------------------------------------------------------------------
    def __del__(self):
    
        pass

#-------------------------------------------------
#
# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("myqueue.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
