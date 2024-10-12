# Copyright (C) 2024, MRIIOT LLC
# All rights reserved.

import ubinascii
import network
import utime


class WLAN:
    def __init__(self, **kwargs):
        self._net = None
        self._ip = "0.0.0.0"
        self._mask = "0.0.0.0"
        self._gateway = "0.0.0.0"
        self._dns = "0.0.0.0"
        self._wait_for_ip = False

    def is_connected(self):
        return self._net.isconnected() if self._net else False

    def mac(self):
        return ubinascii.hexlify(self._net.config('mac')).decode('utf-8') if self._net else None

    def ifconfig(self):
        return self._net.ifconfig() if self._net else ('0.0.0.0', '0.0.0.0', '0.0.0.0', '0.0.0.0')

    def set_ifconfig(self):
        if self._net is None:
            return

        ip_tuple = (self._ip, self._mask, self._gateway, self._dns)
        if "0.0.0.0" not in ip_tuple:
            self._net.ifconfig(ip_tuple)

    def quality(self):
        try:
            return self._net.status('rssi')
        except:
            return 0

    def hostname(self):
        try:
            return network.hostname()
        except:
            return "?"

    def set_hostname(self):
        network.hostname(f"SHARC-{self.mac()[-6:]}")

    def print_info(self):
        print('host={}, mac={}, ip={}, qual={}'.format(
            self.hostname(),
            self.mac(),
            self.ifconfig(),
            self.quality()))

    def connect(self, ssid, password, ip = "0.0.0.0", mask = "0.0.0.0", gateway = "0.0.0.0", dns = "0.0.0.0", wait_for_ip=False):
        self._ip = ip
        self._mask = mask
        self._gateway = gateway
        self._dns = dns
        self._wait_for_ip = wait_for_ip

        self._net = network.WLAN(network.STA_IF)
        self.set_hostname()
        self.set_ifconfig()
        self._net.active(True)
        self._net.config(pm=network.WLAN.PM_NONE)
        # print(self._net.scan())
        if self._net.isconnected():
            # already connected
            pass
        else:
            self._net.connect(ssid, password)

            if self._wait_for_ip is True:
                while self._net.status() != network.STAT_GOT_IP:
                    utime.sleep_ms(500)

        self.print_info()

    def disconnect(self):
        if self._net:
            self._net.disconnect()
