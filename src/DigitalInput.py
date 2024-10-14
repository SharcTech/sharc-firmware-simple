# Copyright (C) 2024, MRIIOT LLC
# All rights reserved.

from machine import Pin
import utime as time


class DigitalInput:
    def __init__(self, name, pin, **kwargs):
        self._name = name
        self._pin_number = pin
        self._pin_instance = Pin(self._pin_number, Pin.IN, Pin.PULL_UP)
        self._last_state = None
        self._current_state = None
        self._change_ts = 0
        self._change_delta = 0

    def read(self, force_change = False):
        self._current_state = self._pin_instance.value()
        if self._current_state == self._last_state and force_change is False:
            return self._name, False, self._current_state, 0
        else:
            self._last_state = self._current_state
            self._change_delta = abs(time.ticks_diff(time.ticks_ms(), self._change_ts))
            self._change_ts = time.ticks_ms()
            return self._name, True, self._current_state, self._change_delta
