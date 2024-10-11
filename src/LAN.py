# Copyright (C) 2022, MRIIOT LLC
# All rights reserved.

import ubinascii
from machine import Pin
import network
import utime


class LAN:
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self._net = None
		self.pin_mdc = 23
		self.pin_mdio = 18
		self.pin_reset = 5

	def is_connected(self):
		return self._net.isconnected() if self._net else False

	def mac(self):
		return ubinascii.hexlify(self._net.config('mac')).decode('utf-8') if self._net else None

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

	def connect(self):
		self._net = network.LAN(
			id=0,
			mdc=Pin(self.pin_mdc),
			mdio=Pin(self.pin_mdio),
			power=Pin(self.pin_reset),
			phy_addr=0,
			phy_type=network.PHY_RTL8201)

		self.set_hostname()

		if self._net.status() != network.ETH_INITIALIZED:
			# already active
			pass
		else:
			self._net.active(True)
			while self._net.status() != network.ETH_GOT_IP:
				utime.sleep_ms(500)

		self.print_info()

	def disconnect(self):
		pass
