# Copyright (C) 2025, MRIIOT LLC
# All rights reserved.

import machine
import utime as time
from micropython import const
import network
from src.LED import LED
from src.LAN import LAN
from src.WLAN import WLAN
from src.MQTTClient import MQTTClient
from src.AirInput import AirInput

_wlan_ssid = "yourssid"
_wlan_password = "yourpassword"
_mqtt_server = "sharc.tech"
_mqtt_port = 1883
_mqtt_username = None
_mqtt_password = None
_mqtt_keepalive = 5

_command_topic = const("sharky/1/command")
_event_topic = const("sharky/1/event")
_ip_zero = const("0.0.0.0")
_is_running = True
_is_connected = False

_led = LED()
_led.white()

_lan = LAN()
_lan.connect(
        ip=_ip_zero,           # set valid ip addresses to make static
        mask=_ip_zero,         # leave all zeros to use dhcp
        gateway=_ip_zero,
        dns=_ip_zero,
        wait_for_ip=True)      # wait to acquire ip address before continuing


#_wlan = WLAN()
#_wlan.connect(
#        ssid=_wlan_ssid,
#        password=_wlan_password,
#        ip=_ip_zero,           # set valid ip addresses to make static
#        mask=_ip_zero,         # leave all zeros to use dhcp
#        gateway=_ip_zero,
#        dns=_ip_zero,
#        wait_for_ip=False)      # wait to acquire ip address before continuing

def _mqtt_message_handler(topic, message, retained, duplicate):
        print ("msg received: {}".format(message))
        if message == "reset":
                machine.reset()

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

_air = AirInput(1, 35, 0, True)

while _is_running is True:
  air_data = _air.read()

  if (air_data):
    for air_key in air_data.keys():
      _mqtt.publish_json("{}/{}".format(_event_topic, air_key),
        {
          "value": air_data[air_key],
        })

  _is_connected = _mqtt.update()

  if _is_connected is True:
    _led.green()
  else:
    _led.red()

_mqtt.disconnect()
#_wlan.disconnect()
_lan.disconnect()
