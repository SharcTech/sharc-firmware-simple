# Copyright (C) 2024, MRIIOT LLC
# All rights reserved.

import machine
from micropython import const
from src.LED import LED
from src.LAN import LAN
from src.WLAN import WLAN
from src.MQTTClient import MQTTClient
from src.DigitalInput import DigitalInput
from src.I2CBus import I2CBus
from src.AnalogInput import AnalogInput

_wlan_ssid = "CC"
_wlan_password = "haptixgames"
_mqtt_server = "sharc.tech"
_mqtt_port = 1883
_mqtt_username = None
_mqtt_password = None
_mqtt_keepalive = 5

_command_topic = const("sharky/command")
_event_topic = const("sharky/event")
_ip_zero = const("0.0.0.0")
_is_running = True

_led = LED()
_led.white()

_lan = LAN()
_lan.connect(
        ip=_ip_zero,           # set valid ip addresses to make static
        mask=_ip_zero,         # leave all zeros to use dhcp
        gateway=_ip_zero,
        dns=_ip_zero,
        wait_for_ip=False)      # wait to acquire ip address before continuing

_wlan = WLAN()
_wlan.connect(
        ssid=_wlan_ssid,
        password=_wlan_password,
        ip=_ip_zero,           # set valid ip addresses to make static
        mask=_ip_zero,         # leave all zeros to use dhcp
        gateway=_ip_zero,
        dns=_ip_zero,
        wait_for_ip=False)      # wait to acquire ip address before continuing

def _mqtt_message_handler(topic, message, retained, duplicate):
        print ("msg received: {}".format(message))
        if message == "reset":
                machine.reset()
        if message == "io":
                global _force_read_io
                _force_read_io = True

_mqtt = MQTTClient()
_mqtt.connect(client_id=_lan.mac(),
        server=_mqtt_server,
        port=_mqtt_port,
        username=_mqtt_username,
        password=_mqtt_password,
        keepalive=_mqtt_keepalive,
        command_topic=_command_topic,
        event_topic=_event_topic,
        message_handler=_mqtt_message_handler)

_pnp = DigitalInput("pnp", 36)
_npn = DigitalInput("npn", 39)
_i2c = I2CBus()
_analog = AnalogInput(_i2c)
_force_read_io = False

while _is_running is True:
        pnp_value = _pnp.read(_force_read_io)
        npn_value = _npn.read(_force_read_io)
        volts_value = _analog.read(_force_read_io)
        amps_value = _analog.read(_force_read_io)
        _force_read_io = False
        _io_changed = False

        if pnp_value[1] is True:
                _io_changed = True
                _mqtt.publish_json("{}/{}".format(_event_topic, pnp_value[0]),
                                   {
                                                "value": pnp_value[2],
                                                "delta": pnp_value[3]
                                        })

        if npn_value[1] is True:
                _io_changed = True
                _mqtt.publish_json("{}/{}".format(_event_topic, npn_value[0]),
                                   {
                                                "value": npn_value[2],
                                                "delta": npn_value[3]
                                        })

        if volts_value[1] is True:
                _io_changed = True
                _mqtt.publish_json("{}/{}".format(_event_topic, volts_value[0]),
                                   {
                                                "value": volts_value[2],
                                                "delta": volts_value[3]
                                        })

        if amps_value[1] is True:
                _io_changed = True
                _mqtt.publish_json("{}/{}".format(_event_topic, amps_value[0]),
                                   {
                                                "value": amps_value[2],
                                                "delta": amps_value[3]
                                        })

        is_connected = _mqtt.update()

        if is_connected is True:
            _led.green()
        else:
            _led.red()

        if _io_changed is True:
            _led.blink(True, period=500, once=False)

_mqtt.disconnect()
_wlan.disconnect()
_lan.disconnect()
