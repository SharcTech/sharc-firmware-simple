# Copyright (C) 2022, MRIIOT LLC
# All rights reserved.


from machine import Timer
from machine import Pin


class LED:
	def __init__(self, **kwargs):
		# internals
		self._pin_blu = Pin(14, Pin.OUT)
		self._pin_grn = Pin(32, Pin.OUT)
		self._pin_red = Pin(33, Pin.OUT)
		self._tmr_blink = None
		self._tmr_on = False
		self._tmr_oneshot = False
		self._current_color = None
		self._last_color = None

	def blue(self):
		if self._current_color == self.blue:
			return
		self._pin_blu.value(1)
		self._pin_grn.value(0)
		self._pin_red.value(0)
		self._current_color = self.blue

	def green(self):
		if self._current_color == self.green:
			return
		self._pin_blu.value(0)
		self._pin_grn.value(1)
		self._pin_red.value(0)
		self._current_color = self.green

	def red(self):
		if self._current_color == self.red:
			return
		self._pin_blu.value(0)
		self._pin_grn.value(0)
		self._pin_red.value(1)
		self._current_color = self.red

	def yellow(self):
		if self._current_color == self.yellow:
			return
		self._pin_blu.value(0)
		self._pin_grn.value(1)
		self._pin_red.value(1)
		self._current_color = self.yellow

	def cyan(self):
		if self._current_color == self.cyan:
			return
		self._pin_blu.value(1)
		self._pin_grn.value(1)
		self._pin_red.value(0)
		self._current_color = self.cyan

	def magenta(self):
		if self._current_color == self.magenta:
			return
		self._pin_blu.value(1)
		self._pin_grn.value(0)
		self._pin_red.value(1)
		self._current_color = self.magenta

	def white(self):
		if self._current_color == self.white:
			return
		self._pin_blu.value(1)
		self._pin_grn.value(1)
		self._pin_red.value(1)
		self._current_color = self.white

	def off(self):
		self._pin_blu.value(0)
		self._pin_grn.value(0)
		self._pin_red.value(0)
		self._current_color = None

	def _cb_blink(self, timer):
		if self._tmr_oneshot is True:
			self._tmr_on = False
			self._tmr_blink.deinit()
		if self._current_color:
			self._last_color = self._current_color
			self.off()
		elif self._last_color:
			self._last_color()

	def blink(self, state, period=500, once=False):
		self._tmr_on = state
		self._tmr_oneshot = True if once is True else False
		if self._tmr_blink and not state:
			self._tmr_blink.deinit()
		elif self._tmr_blink and state:
			self._tmr_blink.init(mode=Timer.ONE_SHOT if once is True else Timer.PERIODIC, period=period, callback=self._cb_blink)
		elif not self._tmr_blink and state:
			self._tmr_blink = Timer(0)
			self._tmr_blink.init(mode=Timer.ONE_SHOT if once is True else Timer.PERIODIC, period=period, callback=self._cb_blink)
