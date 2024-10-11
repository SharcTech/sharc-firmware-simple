# Copyright (C) 2024, MRIIOT LLC
# All rights reserved.


from machine import Pin
from src.LED import LED
from src.LAN import LAN
from src.MQTTClient import MQTTClient

_is_running = True

_led = LED()
_led.white()

_lan = LAN()
_lan.connect()

_mqtt = MQTTClient()
_mqtt.connect(client_id=_lan.mac(),
        server="sharc.tech",
        port=1883,
        username=None,
        password=None,
        keepalive=5)

_digital_pin_number = 36 # 36-pnp, 39-npn
_digital_pin = Pin(_digital_pin_number, Pin.IN, Pin.PULL_UP)
_digital_last_state = None
_digital_current_state = None

while _is_running is True:

        _digital_current_state = _digital_pin.value()
        if _digital_current_state != _digital_last_state:
                _mqtt.publish_json("sharky/event", {("pnp" if _digital_pin_number == 36 else "npn"): _digital_current_state})
                _digital_last_state = _digital_current_state

        if _digital_current_state == 1:
                _led.red()
        else:
                _led.white()

        _mqtt.update()

_mqtt.disconnect()
_lan.disconnect()