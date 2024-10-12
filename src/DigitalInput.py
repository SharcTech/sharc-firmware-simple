# Copyright (C) 2024, MRIIOT LLC
# All rights reserved.

from machine import Pin


class DigitalInput:
    def __init__(self, name, pin, **kwargs):
        self._name = name
        self._pin_number = pin
        self._pin_instance = Pin(self._pin_number, Pin.IN, Pin.PULL_UP)
        self._last_state = None
        self._current_state = None

    def read(self):
        self._current_state = self._pin_instance.value()
        if self._current_state == self._last_state:
            return self._name, False, self._current_state
        else:
            self._last_state = self._current_state
            return self._name, True, self._current_state
