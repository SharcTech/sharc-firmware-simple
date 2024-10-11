#!/bin/sh

export USB_TTL_DEV=/dev/tty.usbserial-B002YRE8
esptool.py -p $USB_TTL_DEV  -b 460800 \
    --before default_reset \
    --after hard_reset \
    --chip esp32  write_flash \
    --flash_mode dio \
    --flash_size detect \
    --flash_freq 40m \
    0x1000 image/bootloader.bin \
    0x9000 image/partition-table.bin \
    0xe000 image/ota_data_initial.bin \
    0x20000 image/micropython.bin
