#!/bin/sh

export USB_TTL_DEV=/dev/tty.usbserial-B002YRE8
mpremote connect $USB_TTL_DEV fs cp -r src :
mpremote connect $USB_TTL_DEV fs cp boot.py :
mpremote connect $USB_TTL_DEV fs cp main.py :

