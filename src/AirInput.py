# Copyright (C) 2025, MRIIOT LLC
# All rights reserved.

from machine import UART
import utime as time
import random


class AirInput:
    def __init__(self, id, rx_pin, tx_pin, simulate=False, **kwargs):
        self._uart = UART(id, baudrate=9600, bits=8, parity=None, stop=1, tx=tx_pin, rx=rx_pin, timeout=1000)
        self._simulate = simulate

    def _processBuffer(self, buffer):
        if int.from_bytes(buffer[0:2], byteorder='big') != 65530:
            print("bad packet preamble")
            return None

        status = int.from_bytes(buffer[2:4], byteorder='big', signed=False)
        print(f"buffer : {buffer}")
        print(f"status : {status & 0xFFFF:016b}")
        air = {
            "hc": 1 if (status & 1 << 0) > 0 else 0,
            "da": 1 if (status & 1 << 1) > 0 else 0,
            "fs": 1 if (status & 1 << 2) > 0 else 0,
            "fan": 1 if (status & 1 << 3) > 0 else 0,
            "nc03": int.from_bytes(buffer[4:6], byteorder='big', signed=False),
            "nc05": int.from_bytes(buffer[6:8], byteorder='big', signed=False),
            "nc10": int.from_bytes(buffer[8:10], byteorder='big', signed=False),
            "nc25": int.from_bytes(buffer[10:12], byteorder='big', signed=False),
            "nc40": int.from_bytes(buffer[12:14], byteorder='big', signed=False),
            "pm1_1": int.from_bytes(buffer[14:16], byteorder='big', signed=False),
            "pm25_1": int.from_bytes(buffer[16:18], byteorder='big', signed=False),
            "pm10_1": int.from_bytes(buffer[18:20], byteorder='big', signed=False),
            "pm1_2": int.from_bytes(buffer[20:22], byteorder='big', signed=False),
            "pm25_2": int.from_bytes(buffer[22:24], byteorder='big', signed=False),
            "pm10_2": int.from_bytes(buffer[24:26], byteorder='big', signed=False),
            "temp": int.from_bytes(buffer[26:28], byteorder='big', signed=True),
            "hum": int.from_bytes(buffer[28:30], byteorder='big', signed=False),
            "tvoc": int.from_bytes(buffer[30:32], byteorder='big', signed=False),
            "eco2": int.from_bytes(buffer[32:34], byteorder='big', signed=False),
            "iaq": int.from_bytes(buffer[34:36], byteorder='big', signed=False)
        }

        return air

    def _generateFakeData(self):
        time.sleep_ms(1200)
        return {
            "hc": random.randint(0, 1),
            "da": random.randint(0, 1),
            "fs": random.randint(0, 1),
            "fan": random.randint(0, 1),
            "nc03": random.randint(0, 100),
            "nc05": random.randint(0, 100),
            "nc10": random.randint(0, 100),
            "nc25": random.randint(0, 100),
            "nc40": random.randint(0, 100),
            "pm1_1": random.randint(0, 100),
            "pm25_1": random.randint(0, 100),
            "pm10_1": random.randint(0, 100),
            "pm1_2": random.randint(0, 100),
            "pm25_2": random.randint(0, 100),
            "pm10_2": random.randint(0, 100),
            "temp": random.randint(1900, 2400),
            "hum": random.randint(3000, 8000),
            "tvoc": random.randint(0, 100),
            "eco2": random.randint(0, 100),
            "iaq": random.randint(100, 900),
        }

    def read(self):
        if self._simulate:
            return self._generateFakeData()
        else:
            buff = b''

            while (len(buff) < 39):
                buff += self._uart.readline()
                print(len(buff))

            return self._processBuffer(buff)
