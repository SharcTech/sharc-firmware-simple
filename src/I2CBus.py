# Copyright (C) 2024, MRIIOT LLC
# All rights reserved.


from micropython import const
from machine import Pin
from machine import SoftI2C


class I2CBus:
	def __init__(self, **kwargs):
		# internals
		self.temp_byte = bytearray(1)
		self.temp_word = bytearray(2)
		self.temp_buffer = bytearray(3)
		self._i2c = SoftI2C(Pin(15),
							Pin(4),
							freq=400000)

	def has_devices(self, device_list):
		i2c_addresses_found = self._i2c.scan()
		i2c_addresses_not_found = [e for e in device_list if e not in i2c_addresses_found]
		i2c_addresses_missing = len(i2c_addresses_not_found) > 0
		if i2c_addresses_missing:
			print("missing devices {}".format(i2c_addresses_not_found))
			return False
		else:
			print("all devices present")
			return True

	def scan(self):
		return self._i2c.scan()

	def write_byte(self, address, register, data):
		self._i2c.writeto_mem(address, register, data, addrsize=8)

	def write_bytes(self, address, register, datas):
		for data in datas:
			self.write_byte(address, register, data)

	def write_word(self, address, register, data):
		self.temp_buffer[0] = register
		self.temp_buffer[1] = data >> 8
		self.temp_buffer[2] = data & 0xff
		self._i2c.writeto(address, self.temp_buffer)

	def read_byte(self, address, register):
		self._i2c.readfrom_mem_into(address, register, self.temp_byte, addrsize=8)
		return self.temp_byte[0]

	def read_word(self, address, register):
		self._i2c.readfrom_mem_into(address, register, self.temp_word, addrsize=8)
		return (self.temp_word[0] << 8) | self.temp_word[1]
