#!/usr/bin/python3
# coding: utf-8
#
# ***********************************************************
#
# Clear Switcher3 Logfiles..
#-----------------------------
import argparse, os, sys

logfile_1 = "switcher3.log"
logfiles = ["switcher3.log.1","switcher3.log.2","switcher3.log.3"]

#*********  delete a file  **********
#----------------------------------------------------------
def remove_file(filename):

    try:
        os.remove(filename) 
    except:
        print ("File {} not found". format(filename))
    finally:
        pass

    return()

#---------------------------------------------------------------
# Program starts here
#---------------------------------------------------------------
if __name__ == "__main__":

    print ("Clearing Switcher3 Logfiles")

    # Base file switcher3.log nur leeren, bleibt bestehen !
    try:
        f=open(logfile_1,'w').close()
    except:
        print ("error file1")
    finally:
        pass

    # die restlichen Logfile entfernen 
    for file in logfiles:
        remove_file(file)

    print ("Switcher3 Logfiles cleared")



