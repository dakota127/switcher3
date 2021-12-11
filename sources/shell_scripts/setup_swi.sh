#!/bin/bash

#  setup switcher

echo "----> Setup Switcher3 <-----"
echo " "
echo "Schritt 1: kopiere Inhalt von dir sources"

file="sources"
if [ -d "$file" ]
then
	echo "$file vorhanden, kopiere inhalt"
	cp -n -v -R sources/* /home/pi/switcher3
	rm -f -R $file	

else echo "dir $file nicht vorhanden, mache nichts"
fi

# adjust permissions for 433 Mhz send module	
chmod 777 433_send/send

# adjust permissions for scripts
chmod 755 shell_scripts/cptest_swi.sh
chmod 755 shell_scripts/remove_swi.sh

echo " "
echo "Schritt 2: kopiere Files für mosquitto"

file="/etc/mosquitto/conf.d/my_mosquitto.conf"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden, remove"
	sudo rm -f $file
fi
echo "$file not found, copy"
sudo cp -n -v mosquitto_stuff/my_mosquitto.conf /etc/mosquitto/conf.d

# Password file 
sudo rm -f my_passw.txt
file="/etc/mosquitto/my_passw.txt"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden, remove"
	sudo rm -f $file
fi

echo "$file not found, also kopiere"
sudo cp -n -v mosquitto_stuff/my_passw.txt /etc/mosquitto


# acl file 
sudo rm -f my_aclfile.txt
file="/etc/mosquitto/my_aclfile.txt"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden, remove"
	sudo rm -f $file
fi

echo "$file not found, also kopiere"
sudo cp -n -v mosquitto_stuff/my_aclfile.txt /etc/mosquitto


# encrypt the passowrd file
echo "encrypt password file..."
sudo mosquitto_passwd -U /etc/mosquitto/my_passw.txt
echo "mosquitto logfile permissions"
sudo chmod 777 /var/log/mosquitto/mosquitto.log
echo "mosquitto user config done"
echo " "

echo "Schritt 3: copy scripts for switcher3"

#
file="/etc/systemd/system/switcher3.service"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden, remove"
	sudo rm -f $file
fi
echo "$file not found, also kopiere"
sudo cp -n -v shell_scripts/switcher3.service /etc/systemd/system/switcher3.service


file="/etc/systemd/system/swserver3.service"
if [ -f "$file" ]
then
	echo "$file bereits vorhanden, remove"
	sudo rm -f $file
fi
	echo "$file not found, also kopiere"
sudo cp -n -v shell_scripts/swserver3.service /etc/systemd/system/swserver3.service

sudo chmod 755 /etc/systemd/system/switcher3.service
sudo chmod 755 /etc/systemd/system/swserver3.service

sudo systemctl enable swserver3.service
sudo systemctl enable switcher3.service

echo "entferne .git Ordner"
sudo rm -rf .git
sudo chown -R pi *
#
echo "Setup for switcher3 done"



