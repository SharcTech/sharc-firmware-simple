# Copyright (C) 2024, MRIIOT LLC
# All rights reserved.

import machine
import utime as time
from src.NOW import NOW
from src.LED import LED
from src.DigitalInput import DigitalInput
from src.I2CBus import I2CBus
from src.AnalogInput import AnalogInput

_is_running = True
_config = {
    "gateway_mac": "FF:FF:FF:FF:FF:FF"
}

_led = LED()
_led.white()

def _esp_message_handler(host, message):
    messages = [x for x in message.decode('utf-8').split("|") if x]
    print(messages)

    if len(messages) == 1:
        return

    if messages[1] == "CMD":
        if messages[2] == "ACT":
            if messages[3] == "RST":
                _is_running = False
                _now.send(host, "|EVT|ACK|{}".format(messages[0]))
            if messages[3] == "IO":
                global _force_read_io
                _force_read_io = True
                _now.send(host, "|EVT|ACK|{}".format(messages[0]))
            if messages[3] == "PING":
                _now.send(host, "|EVT|ACK|{}".format(messages[0]))
        if messages[2] == "CFG":
            global _config
            _config[messages[3]] = messages[4]
            _now.send(host, "|EVT|ACK|{}".format(messages[0]))


_now = NOW(message_handler=_esp_message_handler)
_pnp = DigitalInput("pnp", 36)
_npn = DigitalInput("npn", 39)
_i2c = I2CBus()
_analog = AnalogInput(_i2c)
_force_read_io = False
_last_send = time.time()
_now.send(_config["gateway_mac"], "|EVT|AVAIL|1")

while _is_running is True:
        pnp_value = _pnp.read(_force_read_io)
        npn_value = _npn.read(_force_read_io)
        volts_value = _analog.read(_force_read_io)
        amps_value = _analog.read(_force_read_io)
        _force_read_io = False
        _io_changed = False

        if pnp_value[1] is True:
            _io_changed = True
            _now.send(_config["gateway_mac"], "|EVT|IO|{}|{}|{}".format(pnp_value[0], pnp_value[2], pnp_value[3]))

        if npn_value[1] is True:
            _io_changed = True
            _now.send(_config["gateway_mac"], "|EVT|IO|{}|{}|{}".format(npn_value[0], npn_value[2], npn_value[3]))

        if volts_value[1] is True:
            _io_changed = True
            _now.send(_config["gateway_mac"], "|EVT|IO|{}|{}|{}".format(volts_value[0], volts_value[2], volts_value[3]))

        if amps_value[1] is True:
            _io_changed = True
            _now.send(_config["gateway_mac"], "|EVT|IO{}|{}|{}".format(amps_value[0], amps_value[2], amps_value[3]))

        if _io_changed is True:
            _led.off()
            time.sleep_ms(10)

        _now.update()

        if abs(time.ticks_diff(time.ticks_ms(), _last_send)) > 30000:
            _last_send = time.ticks_ms()
            _now.send(_config["gateway_mac"], "|EVT|STAT|{}".format(_now.stats()))

_now.send(_config["gateway_mac"], "|EVT|AVAIL|0")
machine.reset()