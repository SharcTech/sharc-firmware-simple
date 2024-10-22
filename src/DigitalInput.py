# Copyright (C) 2024, MRIIOT LLC
# All rights reserved.

from machine import Pin
import utime as time


class DigitalInput:
    def __init__(self, name, pin, mode="count", **kwargs):
        self._name = name
        self._pin_number = pin
        self._pin_instance = Pin(self._pin_number, Pin.IN, Pin.PULL_UP)
        self._mode = mode
        self._last_state = None
        self._current_state = None
        self._change_ts = 0
        self._change_delta = 0
        self._count = 0

    def read(self, force_change = False):
        if self._mode == "switch":
            return self._read_switch(force_change)
        elif self._mode == "count":
            return self._read_counter(force_change)
        else:
            return self._name, False, self._current_state, 0

    def _read_switch(self, force_change = False):
        self._current_state = self._pin_instance.value()
        if self._current_state == self._last_state and force_change is False:
            return self._name, False, self._current_state, 0
        else:
            self._last_state = self._current_state
            self._change_delta = abs(time.ticks_diff(time.ticks_ms(), self._change_ts))
            self._change_ts = time.ticks_ms()
            return self._name, True, self._current_state, self._change_delta

    def _read_counter(self, force_change = False):
        self._current_state = self._pin_instance.value()
        if self._current_state == self._last_state and force_change is False:
            return self._name, False, self._count, 0
        # rising edge
        elif (self._last_state == 0 and self._current_state == 1) or force_change is True:
            self._last_state = self._current_state
            self._change_delta = abs(time.ticks_diff(time.ticks_ms(), self._change_ts))
            self._change_ts = time.ticks_ms()
            if force_change is False:
                self._count = self._count + 1
            return self._name, True, self._count, self._change_delta
        else:
            self._last_state = self._current_state
            return self._name, False, self._count, 0

    def set_counter(self, value):
        self._count = int(value)
