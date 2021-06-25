#!/bin/bash

#  remove switcher 3

echo "Stop services for switcher3"
#
systemctl stop switcher3.service
systemctl stop swserver3.service

echo "remove services for switcher3"
systemctl disable switcher3.service
systemctl disable swserver3.service


file="/etc/systemd/system/switcher3.service"
if [ -f "$file" ]
then
	echo "$file  vorhanden, remove"
	rm -f $file
fi


file="/etc/systemd/system/swserver3.service"
if [ -f "$file" ]
then
	echo "$file  vorhanden, remove"
	rm -f $file
fi

#

echo "services for switcher3 removed"



