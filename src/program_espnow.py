# Copyright (C) 2024, MRIIOT LLC
# All rights reserved.

import machine
import struct
import utime as time
import os
from src.NOW import NOW
from src.LED import LED
from src.DigitalInput import DigitalInput
from src.I2CBus import I2CBus
from src.AnalogInput import AnalogInput

_is_running = True
_config = {
    "p2p.gateway": b'\xff\xff\xff\xff\xff\xff',
    "sensor.s0.mode": "count",
    "sensor.s1.mode": "count"
}

_led = LED()
_led.green()

def _esp_message_handler(host, message):
    messages = [x for x in message.split("|") if x]
    print(messages)

    if len(messages) == 1:
        return

    if messages[1] == "CMD":
        if messages[2] == "ACT":
            if messages[3] == "RST":
                global _is_running
                _is_running = False
                _now.send(host, "|EVT|ACK|{}".format(messages[0]))
            if messages[3] == "IO":
                global _force_read_io
                _force_read_io = True
                _now.send(host, "|EVT|ACK|{}".format(messages[0]))
            if messages[3] == "COUNTER":
                global _pnp
                global _npn
                _pnp.set_counter(messages[4])
                _npn.set_counter(messages[4])
                _now.send(host, "|EVT|ACK|{}".format(messages[0]))
            if messages[3] == "PING":
                _now.send(host, "|EVT|ACK|{}".format(messages[0]))
        if messages[2] == "CFG":
            global _config
            _config[messages[3]] = messages[4]
            _now.send(host, "|EVT|ACK|{}".format(messages[0]))


_now = NOW(message_handler=_esp_message_handler)
_pnp = DigitalInput("pnp", 36, _config["sensor.s0.mode"])
_npn = DigitalInput("npn", 39, _config["sensor.s1.mode"])
_i2c = I2CBus()
_analog = AnalogInput(_i2c)
_force_read_io = True
_last_send = time.time()
_now.send(_config["p2p.gateway"], "|EVT|AVAIL|1")
_led.white()

while _is_running is True:
        pnp_value = _pnp.read(_force_read_io)
        npn_value = _npn.read(_force_read_io)
        volts_value = _analog.read(_force_read_io)
        amps_value = _analog.read(_force_read_io)
        _force_read_io = False
        _io_changed = False

        if pnp_value[1] is True:
            _io_changed = True
            msg = "|EVT|IO|%s|%d|%d" % (pnp_value[0], pnp_value[2], pnp_value[3])
            _now.send(_config["p2p.gateway"], msg.encode())

        if npn_value[1] is True:
            _io_changed = True
            msg = "|EVT|IO|%s|%d|%d" % (npn_value[0], npn_value[2], npn_value[3])
            _now.send(_config["p2p.gateway"], msg.encode())

        if volts_value[1] is True:
            _io_changed = True
            value = (volts_value[2] * 0.000384615 - 0) / (10 - 0) * (10 - 0) + 0
            msg = "|EVT|IO|%s|%f|%d" % (volts_value[0], value, volts_value[3])
            _now.send(_config["p2p.gateway"], msg.encode())

        if amps_value[1] is True:
            _io_changed = True
            value = (amps_value[2] * 0.00075 - 4) / (20 - 4) * (20 - 4) + 4
            msg = "|EVT|IO|%s|%f|%d" % (amps_value[0], value, amps_value[3])
            _now.send(_config["p2p.gateway"], msg.encode())

        if _io_changed is True:
            _led.off()
            time.sleep_ms(10)
            _led.white()

        _now.update()

        if abs(time.ticks_diff(time.ticks_ms(), _last_send)) > 30000:
            _last_send = time.ticks_ms()
            _now.send(_config["p2p.gateway"], "|EVT|STAT|{}".format(_now.stats()))

_led.red()
_now.send(_config["p2p.gateway"], "|EVT|AVAIL|0")
machine.reset()