#!/usr/bin/python
# coding: utf-8

#-----------------------------------------------------
#   Module MyPrint 
#   
#   TO replace the print statement used in Python Programs
#
#   2 Classes are defined here: MyLog und MyPrint
#
#   For demo see check out the two testscripts printest_1.py und printest_2.py
#
#   August 2018 Peter K. Boxler
#------------------------------------------------------
# Std Python Modules
import os, datetime
from logging.handlers import RotatingFileHandler
import logging


# ***********************************************************
# 	Class MyLog 
#   
#   enkapsuliert Logging to File
#  
# *********************************************************  

class MyLog:
    """
        File-like object
        All print statements used for debugging can be redirected to this file
    """
    logger=0
    filehandler=0
    consolehandler=0
    
    def __init__(self, filename, appname, debug_level):
      
#----------------------------------------------------------------------
        """
        Creates a rotating log
        """
        MyLog.logger = logging.getLogger(appname)       # setup Logger
        MyLog.logger.setLevel(logging.DEBUG)

            
#        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        formatter = logging.Formatter('%(asctime)s - %(name)s: %(message)s')
        MyLog.consolehandler = logging.StreamHandler()  # setup Stremhandler
        if debug_level==0:
            MyLog.consolehandler.setLevel(logging.ERROR)
        if debug_level==1:
            MyLog.consolehandler.setLevel(logging.WARNING)
        if debug_level==2:
            MyLog.consolehandler.setLevel(logging.INFO)
        if debug_level==3:
            MyLog.consolehandler.setLevel(logging.DEBUG)

        MyLog.logger.addHandler(MyLog.consolehandler)

    
    # add a rotating handler
    
        MyLog.filehandler = RotatingFileHandler (filename, maxBytes=300000,backupCount=3)
        if debug_level==0:
            MyLog.filehandler.setLevel(logging.ERROR)
        if debug_level==1:
            MyLog.filehandler.setLevel(logging.WARNING)
        if debug_level==2:
            MyLog.filehandler.setLevel(logging.INFO)
        if debug_level==3:
            MyLog.filehandler.setLevel(logging.DEBUG)
        
        MyLog.filehandler.setFormatter(formatter)
        MyLog.logger.addHandler(MyLog.filehandler)

        
 #--- Public Method 
 # zum setzten der level der beiden handler.
    def set_level(self,debug_level):

        if debug_level==0:
             MyLog.consolehandler.setLevel(logging.ERROR)
        if debug_level==1:
             MyLog.consolehandler.setLevel(logging.WARNING)
        if debug_level==2:
             MyLog.consolehandler.setLevel(logging.INFO)
        if debug_level==3:
             MyLog.consolehandler.setLevel(logging.DEBUG)

        if debug_level==0:
             MyLog.filehandler.setLevel(logging.ERROR)
        if debug_level==1:
             MyLog.filehandler.setLevel(logging.WARNING)
        if debug_level==2:
             MyLog.filehandler.setLevel(logging.INFO)
        if debug_level==3:
             MyLog.filehandler.setLevel(logging.DEBUG)
        

#  Ende Class Defintion MyLog ------------------------------------
#


# ***********************************************************
# 	Class MyPrint 
#   
#   enkapsuliert Logging to File
#  
# *********************************************************  

class MyPrint:
# Matrix für debug-Output
#
    DEBUG_LEVEL0=0
    DEBUG_LEVEL1=1
    DEBUG_LEVEL2=2
    DEBUG_LEVEL3=3


    dinstance=0     # class variable
    log_only=0
    
    def __init__(self, appname, debug_level, logfile):       # Konstruktor
      

            
        MyPrint.dinstance = MyLog (logfile, appname, debug_level)  # instanz der MyLog Klasse erstellen
    
# 
# Public Method für Logging aus dem Applikationsprogramm
#-------------------------------------------------------------
    def myprint(self,level_in,meldung):
    
        if level_in==0:
            MyPrint.dinstance.logger.error(meldung)
        elif level_in==1:
            MyPrint.dinstance.logger.warning(meldung)
        elif level_in==2:
            MyPrint.dinstance.logger.info(meldung)
        elif level_in==3:
            MyPrint.dinstance.logger.debug(meldung)
        else:
             MyPrint.dinstance.logger.critical("MyPrint: debug-Level falsch !")
                      
# 
# Public Method for Logging Error in exc_info aus dem Applikationsprogramm
#-------------------------------------------------------------
               
    def myprint_exc(self,meldung):
        MyPrint.dinstance.logger.critical(meldung,exc_info=True)


# Public Method for setup des Logging Levels. 
# die App muss das zuerst aus den Commandline Parms holen
#-------------------------------------------------------------
         
    def set_debug_level(self,level):
        MyPrint.dinstance.set_level(level)        

#-------------Terminate Action PArt --------------------------------------
#------------------------------------------------------------------------
    def __del__(self):
    
        pass


#-----------------------------------------------------------

