#!/usr/bin/python
# coding: utf-8
import subprocess
#
zeilen=[]

p = subprocess.Popen("tail -n 40 switcher3.log", stdout=subprocess.PIPE, shell=True)
#p = subprocess.call(["tail", "-n 40", "switcher2.log"], stdout=subprocess.PIPE)
(output, err) = p.communicate()
 
## Wait for date to terminate. Get return returncode ##
p_status = p.wait()
print (type(output))
print ("Command output : \n", output)
print ("Command exit status/return code : ", p_status)

#output = "Ho Hütt ändern"
output = str(output) + str('üüüüü\n')       # für test mit umlauten im log

# alter test, nicht nötig, aber bleibt drin..
#if type(output) is str:
#    print ("type ist str")
#    pass
#else:
#    try:
#        output=output.decode()
#    except:
#        print ("switcher2.log string kann nicht decodiert werden")
#        output = "Fehler im Server:\nswitcher2.log string kann nicht decodiert werden\nEnthält ev. Umlaute"
#

zeilen = list(output.split("\n"))   # convert string mit NewLine into list

print ("nach split")
for item in zeilen:
    print (item)


print ("----nun noch ps commend ----------------------")
p = subprocess.Popen("ps -ax | grep python3", stdout=subprocess.PIPE, shell=True)
#p = subprocess.call(["tail", "-n 40", "switcher2.log"], stdout=subprocess.PIPE)
(output, err) = p.communicate()
 
## Wait for date to terminate. Get return returncode ##
p_status = p.wait()
if p_status > 0:
    print (" Fehler nach command ausführung:{}".format(p_status))
else:
    output = output.decode()
    output = str(output)
    zeilen = list(output.split("\n"))   # convert string mit NewLine into list

    zeilen.pop()
    zeilen.pop()
    zeilen.pop()

    swserver = False
    switcher = False
    for item in zeilen:
        print (item[27:])
        if item.find("swserver3") >0: swserver = True
        if item.find("switcher3") >0: switcher = True
    
    if swserver: 
        print ("swserver läuft")
    else:
        print ("swserver läuft NICHT")
    if switcher: 
        print ("switcher läuft")
    else:
        print ("switcher läuft NICHT")

print ("\nProgramm fertig")
#----------------------------