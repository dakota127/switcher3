

https://www.raspberrypi.org/documentation/linux/usage/systemd.md



Edit files
nano switcher3.service
nano swserver3.service



File for swserver3

------------------------
[Unit]
Description=swserver33
After=network.target

[Service]
ExecStart=/usr/bin/python3 -u swserver3.py
WorkingDirectory=/home/pi/switcher3
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
--------------------

ps -ax |grep python3




sudo cp switcher3.service /etc/systemd/system/switcher3.service

sudo cp swserver3.service /etc/systemd/system/swserver3.service


Start stop:
sudo systemctl start swserver3.service
sudo systemctl stop swserver3.service

sudo systemctl start switcher3.service
sudo systemctl stop switcher3.service


Enable
sudo systemctl enable swserver3.service
sudo systemctl enable switcher3.service