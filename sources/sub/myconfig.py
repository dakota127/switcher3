#!/usr/bin/python
# coding: utf-8
#
# ***********************************************************
# 	Class ConfigRead 
#   
#   reads a Config File in format .ini
#
#   This Class inherits from the MyPrint Class
#
#   
#    Provides a single public methods called config_read 
#   
#   Input parm is a Python dictionary with key-value pairs 
#   Existing keys are filled from the configfile
#   There can be more keys in the configfile but they are not processed - only those 
#   keys that exists in the passed dir.
#   The configfile can also be noexisting - in the case all key-value pairs remein unchanged.
# 
#   Test this class using testprogram testconfig.py
#
#   August 2018, Peter K. Boxler
#
## ***** Imports ******************************
import sys, getopt, os
from configparser import SafeConfigParser
from sub.myprint import MyPrint
from datetime import date, datetime
# ***** Konstanten *****************************

DEBUG_LEVEL0=0
DEBUG_LEVEL1=1
DEBUG_LEVEL2=2
DEBUG_LEVEL3=3
#

#-------------------------------------------------
#   function to read configfile
#   all parameters are passed in directory configval
#-------------------------------------------------
#----------------------------------------------------
# Class Definition ConfigRead, inherits from MyPrint
#----------------------------------------------------
class ConfigRead (MyPrint):
    ' klasse ConfigRead '
    instzahler=0               # Class Variable
    
#--- INit Methode of this Class ----------------------------    
    def __init__(self, debug_level):  # Init Funktion
        self.nummer = ConfigRead.instzahler
        self.debug = debug_level        
        self.myprint (DEBUG_LEVEL2,"--> ConfigRead init called")
        self.counter=0
        ConfigRead.instzahler +=1            # increase instance counter
        self.parser=0
        self.ret = 0
        self.printstring = "--> ConfigRead: "       
        self.configfile = ""
        
        
        
#--- Public Method config_read  of this Class---------------------------- 
#   Parameter value is a Python dictionary
#-------------------------------------------------------------------
    def config_read(self, configfile, section, values):
        self.counter=0
        self.myprint (DEBUG_LEVEL3,self.printstring + "configRead called, File: {}, Section:{} ".format(self.configfile,section))
             
        self.configfile = configfile             # Config Filename is passed
        self.section=section               # Section ID is passed


        self.parser = SafeConfigParser()         # create Instance of SafeConfigParser Class
        
        self.myprint (DEBUG_LEVEL2, self.printstring + "Name configfile: {} ".format(self.configfile) )

        if not os.path.isfile(self.configfile):
            self.myprint (DEBUG_LEVEL0, self.printstring + "Configfile {} not found".format(self.configfile))
            return(99)
            
        fp = open(self.configfile)   
        ret=self.parser.readfp (fp)  
#        ret=self.parser.read(self.configfile)
  
        if self.parser.has_section(self.section):
            pass 
        else:
            self.myprint (DEBUG_LEVEL0,self.printstring + "Section {} missing in Configfile {}".format(self.section,self.configfile)) 
            return(9)

        if self.debug > DEBUG_LEVEL2:
            for name, value in self.parser.items(self.section):   # returns a list of tuples containing the name-value pairs.
                print ("Name: {}  Value: {} ".format(name, value))
        pass
        for name, value in self.parser.items(self.section):     # returns a list of tuples containing the name-value pairs.
            if name in values:
                self.myprint (DEBUG_LEVEL3,self.printstring + "value: {} found in dir".format(name)) 
                values[name] = value  
                self.counter +=1    # anzahl gefundene Name erhöhen
            else :  
                self.myprint (DEBUG_LEVEL3,self.printstring + "value: {} found in file but not in dir".format(name)) 
              
        if self.counter ==0:
            self.myprint (DEBUG_LEVEL2,self.printstring + "zero entries match dir in program for section {}".format(self.section)) 
            self.ret=8
        else: self.ret=0
        fp.close()
 
        return(self.ret)


#--- Methode get_value dieser Klasse ---------------------------- 
#   Parameter values ist Python List   
#  definiert in swcfg_switcher.py   
    def get_value(self, values,name):
        self.myprint (DEBUG_LEVEL2,self.printstring + "get_value {} called".format (name))
    
        try:
            u=values.index(name) + 1           # wo kommt der gelieferte name vor (index)
            return(values[u])
        except:
            self.myprint (DEBUG_LEVEL0, self.printstring + "Name {} nicht gefunden".format(name))
        
            return(9999)




# --------------------------

            
# *************************************************
# Program starts here
# *************************************************

# ----- MAIN --------------------------------------
if __name__ == "__main__":
    print ("configread.py ist nicht aufrufbar auf commandline")
    sys.exit(2)
    
#**************************************************************
#  That is the end
#***************************************************************
#