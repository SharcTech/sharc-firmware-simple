#!/bin/sh

export USB_TTL_DEV=/dev/tty.usbserial-B002YRE8
esptool.py -p $USB_TTL_DEV erase_flash
