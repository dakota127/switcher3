#!/bin/bash

#  setup switcher

echo "----> Kopieren Testprogramme Switcher3 <-----"
echo " "
file="testscripts"
if [ -d "$file" ]
then
	echo "$file vorhanden, kopiere inhalt"
	cp -n -v -R $file/*.* /home/pi/switcher3

else echo "dir $file nicht vorhanden, mache nichts"
fi

echo " "
echo "Kopieren fertig."




