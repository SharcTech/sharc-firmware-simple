# Copyright (C) 2022, MRIIOT LLC
# All rights reserved.

# l99
from src.lib.l99.injection.ComposableService import ComposableService
# mp
from micropython import const
from machine import Pin
from machine import SoftI2C
# const
_LOG_PFX = const('I2C')


class I2CBus(ComposableService):
	def __init__(self, service_container, **kwargs):
		super().__init__(service_container, **kwargs)
		self._logger.debug(_LOG_PFX, 'create, cfg={}'.format(self.config()))
		# internals
		self.temp_byte = bytearray(1)
		self.temp_word = bytearray(2)
		self.temp_buffer = bytearray(3)
		self._i2c = SoftI2C(Pin(self.config()['pin']['scl']),
							Pin(self.config()['pin']['sda']),
							freq=self.config()['freq'])

	def has_devices(self, device_list):
		i2c_addresses_found = self._i2c.scan()
		i2c_addresses_not_found = [e for e in device_list if e not in i2c_addresses_found]
		i2c_addresses_missing = len(i2c_addresses_not_found) > 0
		if i2c_addresses_missing:
			self._logger.error(_LOG_PFX, "missing devices {}".format(i2c_addresses_not_found))
			return False
		else:
			self._logger.info(_LOG_PFX, "all devices present")
			return True

	def scan(self):
		# return [self._to_hex(address) for address in self._i2c.scan()]
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

		# if self._logger.is_trace():
		#	data_b = self._logger.to_bitstring(data)
		#	word_big_b = self._logger.to_bitstring(int.from_bytes(self.temp_buffer[1:3], "big"))
		#	word_little_b = self._logger.to_bitstring(int.from_bytes(self.temp_buffer[1:3], "little"))
		#	self._logger.trace(_LOG_PFX, f'write_word::address={hex(address)}, register={hex(register)}, data={data}, data_b={data_b}, word_big_b={word_big_b}, word_little_b={word_little_b}')

		self._i2c.writeto(address, self.temp_buffer)

	def read_byte(self, address, register):
		self._i2c.readfrom_mem_into(address, register, self.temp_byte, addrsize=8)
		return self.temp_byte[0]

	def read_word(self, address, register):
		self._i2c.readfrom_mem_into(address, register, self.temp_word, addrsize=8)

		# if self._logger.is_trace():
		#	word_big_b = self._logger.to_bitstring(int.from_bytes(self.temp_word, "big"))
		#	word_big_i = int.from_bytes(self.temp_word, "big")
		#	word_little_i = int.from_bytes(self.temp_word, "little")
		#	word_shifted_i = (self.temp_word[0] << 8) | self.temp_word[1]
		#	self._logger.trace(_LOG_PFX, f'read_word::address={hex(address)}, register={hex(register)}, word={self.temp_word}, word_big_b={word_big_b}, word_big_i={word_big_i}, word_little_i={word_little_i}, word_shifted={word_shifted_i}')

		return (self.temp_word[0] << 8) | self.temp_word[1]
