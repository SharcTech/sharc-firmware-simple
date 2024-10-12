# Copyright (C) 2024, MRIIOT LLC
# All rights reserved.

import ubinascii
from machine import Pin
import network
import utime


class LAN:
	def __init__(self, **kwargs):
		self._net = None
		self._pin_mdc = 23
		self._pin_mdio = 18
		self._pin_reset = 5
		self._ip = "0.0.0.0"
		self._mask = "0.0.0.0"
		self._gateway = "0.0.0.0"
		self._dns = "0.0.0.0"
		self._wait_for_ip = False

	def is_connected(self):
		return self._net.isconnected() if self._net else False

	def mac(self):
		return ubinascii.hexlify(self._net.config('mac')).decode('utf-8') if self._net else None

	def set_ifconfig(self):
		if self._net is None:
			return
		ip_tuple = (self._ip, self._mask, self._gateway, self._dns)
		if "0.0.0.0" not in ip_tuple:
			self._net.ifconfig(ip_tuple)

	def ifconfig(self):
		return self._net.ifconfig() if self._net else ('0.0.0.0', '0.0.0.0', '0.0.0.0', '0.0.0.0')

	def quality(self):
		return 100 if self.is_connected() else 0

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

	def connect(self, ip = "0.0.0.0", mask = "0.0.0.0", gateway = "0.0.0.0", dns = "0.0.0.0", wait_for_ip = False):
		self._ip = ip
		self._mask = mask
		self._gateway = gateway
		self._dns = dns
		self._wait_for_ip = wait_for_ip

		self._net = network.LAN(
			id=0,
			mdc=Pin(self._pin_mdc),
			mdio=Pin(self._pin_mdio),
			power=Pin(self._pin_reset),
			phy_addr=0,
			phy_type=network.PHY_RTL8201)

		self.set_hostname()
		self.set_ifconfig()

		if self._net.status() != network.ETH_INITIALIZED:
			# already active
			pass
		else:
			self._net.active(True)
			if self._wait_for_ip is True:
				while self._net.status() != network.ETH_GOT_IP:
					utime.sleep_ms(500)

		self.print_info()

	def disconnect(self):
		pass
