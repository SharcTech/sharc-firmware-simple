# Copyright (C) 2024, MRIIOT LLC
# All rights reserved.


from micropython import const
import math
import utime as time
# const
# BIT 15
_ADS_OS_NONE = const(0b0000000000000000)
_ADS_OS_STRT = const(0b1000000000000000)
# BIT 14:12
_ADS_MUX_CH0_GND = const(0b0100000000000000)
_ADS_MUX_CH1_GND = const(0b0101000000000000)
_ADS_MUX_CH2_GND = const(0b0110000000000000)
_ADS_MUX_CH3_GND = const(0b0111000000000000)
_ADS_MUX_CH0_CH1 = const(0b0000000000000000)
_ADS_MUX_CH0_CH3 = const(0b0001000000000000)
_ADS_MUX_CH1_CH3 = const(0b0010000000000000)
_ADS_MUX_CH2_CH3 = const(0b0011000000000000)
# BIT 11:09
_ADS_PGA_0256 = const(0b0000101000000000)
_ADS_PGA_0512 = const(0b0000100000000000)
_ADS_PGA_1024 = const(0b0000011000000000)
_ADS_PGA_2048 = const(0b0000010000000000)
_ADS_PGA_4096 = const(0b0000001000000000)
_ADS_PGA_6144 = const(0b0000000000000000)
# BIT 08
_ADS_MODE_SNGL = const(0b0000000100000000)
_ADS_MODE_CONT = const(0b0000000000000000)
# BIT 07:05
_ADS_SPS_860 = const(0b0000000011100000)
_ADS_SPS_745 = const(0b0000000011000000)
_ADS_SPS_250 = const(0b0000000010100000)
_ADS_SPS_128 = const(0b0000000010000000)
_ADS_SPS_064 = const(0b0000000001100000)
_ADS_SPS_032 = const(0b0000000001000000)
_ADS_SPS_016 = const(0b0000000000100000)
_ADS_SPS_008 = const(0b0000000000000000)
# BIT 04
_ADS_COMP_TRAD = const(0b0000000000000000)
_ADS_COMP_WIND = const(0b0000000000010000)
# BIT 03
_ADS_POL_LOW = const(0b0000000000000000)
_ADS_POL_HI = const(0b0000000000001000)
# BIT 02
_ADS_LAT_NON = const(0b0000000000000000)
_ADS_LAT_LAT = const(0b0000000000000100)
# BIT 01:00
_ADS_QUE_ONE = const(0b0000000000000000)
_ADS_QUE_TWO = const(0b0000000000000001)
_ADS_QUE_THR = const(0b0000000000000010)
_ADS_QUE_NON = const(0b0000000000000011)
# other
_I2C_ADDR = const(0x48)
_I2C_REG_CONV = const(0x00)
_I2C_REG_CONF = const(0x01)


class AnalogInput:
    def __init__(self, i2c, **kwargs):
        self._i2c = i2c
        self._chip_found = False
        self._current_channel = 0
        self._ch_min = 0
        self._ch_max = 1

        base = _ADS_OS_STRT | _ADS_PGA_4096 | _ADS_MODE_SNGL | _ADS_SPS_860 | _ADS_COMP_TRAD | _ADS_POL_LOW | _ADS_LAT_NON | _ADS_QUE_NON

        self._channels = {
            0: {
                'name': "0-10V",
                'config': base | _ADS_MUX_CH0_GND,
                'previous': 0,
                'current': 0,
                'trip': 0,
                'changed': False,
                'change_ts': 0,
                'change_delta': 0,
                'first': True,
                'deadband': 100
            },
            1: {
                'name': "4-20mA",
                'config': base | _ADS_MUX_CH1_GND,
                'previous': 0,
                'current': 0,
                'trip': 0,
                'changed': False,
                'change_ts': 0,
                'change_delta': 0,
                'first': True,
                'deadband': 100
            },
            2: {
                'name': 'ai2',
                'config': base | _ADS_MUX_CH2_GND,
                'previous': 0,
                'current': 0,
                'trip': 0,
                'changed': False,
                'change_ts': 0,
                'change_delta': 0,
                'first': True,
                'deadband': 100
            },
            3: {
                'name': 'ai3',
                'config': base | _ADS_MUX_CH3_GND,
                'previous': 0,
                'current': 0,
                'trip': 0,
                'changed': False,
                'change_ts': 0,
                'change_delta': 0,
                'first': True,
                'deadband': 100
            }
        }

    def read(self, force_change=False):
        if force_change is True:
            for ch_key, ch_val in self._channels.items():
                ch_val['first'] = True

        while self._is_busy():
            pass

        channel_id = self._current_channel      # cache channel id
        changed, channel_name, value = self._read_conversion()
        self._next_channel()                    # change channel
        self._request_conversion()
        if changed is True:
            self._channels[channel_id]['change_delta'] = abs(time.ticks_diff(time.ticks_ms(), self._channels[channel_id]['change_ts']))
            self._channels[channel_id]['change_ts'] = time.ticks_ms()

        return channel_name, changed, value, self._channels[channel_id]['change_delta'] if changed is True else 0

    def _is_busy(self):
        return self._i2c.read_word(_I2C_ADDR, _I2C_REG_CONF) >> 15 == 0

    def _read_conversion(self):
        reg00 = self._i2c.read_word(_I2C_ADDR, _I2C_REG_CONV)
        reg00 = reg00 if reg00 < 32768 else reg00 - 65536
        channel = self._channels[self._current_channel]

        trip = math.fabs(reg00 - channel['trip']) > channel['deadband']
        if channel['first']:
            channel['trip'] = reg00
            channel['changed'] = True
            channel['first'] = False
        elif trip:
            channel['trip'] = reg00
            channel['changed'] = True
        else:
            channel['changed'] = False

        channel['previous'] = channel['current']
        channel['current'] = reg00

        return channel['changed'], channel['name'], channel['current']

    def _next_channel(self):
        self._current_channel = self._current_channel + 1 \
            if self._current_channel + 1 <= self._ch_max \
            else self._ch_min

    def _request_conversion(self):
        self._i2c.write_word(_I2C_ADDR, _I2C_REG_CONF, self._channels[self._current_channel]['config'])
