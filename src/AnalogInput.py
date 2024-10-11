# Copyright (C) 2022, MRIIOT LLC
# All rights reserved.

# l99
import src.lib.l99.organizer as organizer
from src.lib.l99.injection.ComposableService import ComposableService
# mp
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
_LOG_PFX = const('AIO')


class AnalogInput(ComposableService):
    def __init__(self, service_container, **kwargs):
        super().__init__(service_container, **kwargs)
        self._logger.debug(_LOG_PFX, 'create, cfg={}'.format(self.config()))
        # dependencies
        self._i2c = None
        # internals
        self._chip_found = False
        self._current_channel = self.config()['channel']['min']
        # cfg holders
        self._cfg_devices = self.config()['devices']
        self._cfg_ch_min = self.config()['channel']['min']
        self._cfg_ch_max = self.config()['channel']['max']

        base = _ADS_OS_STRT | _ADS_PGA_4096 | _ADS_MODE_SNGL | _ADS_SPS_860 | _ADS_COMP_TRAD | _ADS_POL_LOW | _ADS_LAT_NON | _ADS_QUE_NON

        # too low deadband causes client queue to fill up making device unusable
        #  set a hard low threshold or rate limit based on testing
        #  relying on api/app to control deadband threshold is not sufficient
        #  https://github.com/SharcTech/sharc-firmware/issues/20

        self._channels = {
            0: {
                'name': organizer.SENSOR_S2,
                'config': base | _ADS_MUX_CH0_GND,
                'previous': 0,
                'current': 0,
                'trip': 0,
                'changed': False,
                'change_ts': 0,
                'change_delta': 0,
                'first': True,
                'deadband': 100 if self._config['sensor'][organizer.SENSOR_S2]['deadband'] < 100 else self._config['sensor'][organizer.SENSOR_S2]['deadband']
            },
            1: {
                'name': organizer.SENSOR_S3,
                'config': base | _ADS_MUX_CH1_GND,
                'previous': 0,
                'current': 0,
                'trip': 0,
                'changed': False,
                'change_ts': 0,
                'change_delta': 0,
                'first': True,
                'deadband': 100 if self._config['sensor'][organizer.SENSOR_S3]['deadband'] < 100 else self._config['sensor'][organizer.SENSOR_S3]['deadband']
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

        # self._logger.trace(_LOG_PFX, self._channels)

    def inject(self):
        self._i2c = self._sc.resolve(organizer.SVC_NAME_I2C_BUS)
        return self

    def start(self):
        if self._i2c.has_devices(self._cfg_devices):
            self._chip_found = True
            # raise Exception(f'devices not found on i2c bus {self.config()["devices"]}')

        return self

    def read(self, force_change=False):
        if force_change is True:
            for ch_key, ch_val in self._channels.items():
                ch_val['first'] = True

        if not self._chip_found:
            return 'bad', False, 0, 0

        if not self._is_busy():

            # if self._logger.is_trace():
            #    self._logger.trace('AI', f'read::chip_free')

            changed, channel_name, value = self._read_conversion()
            self._next_channel()
            self._request_conversion()

            if changed is True:
                self._channels[self._current_channel]['change_delta'] = abs(time.ticks_diff(time.ticks_ms(), self._channels[self._current_channel]['change_ts']))
                self._channels[self._current_channel]['change_ts'] = time.ticks_ms()
                # self._logger.debug(_LOG_PFX, 'analog: change_delta:{}, change_ts:{}'.format(self._channels[self._current_channel]['change_delta'], self._channels[self._current_channel]['change_ts']))

            return channel_name, changed, value, self._channels[self._current_channel]['change_delta'] if changed is True else 0
            # TODO: return 0 delta or continue increasing current delta

        # if self._logger.is_trace():
        #     self._logger.trace(_LOG_PFX, f'read::chip_busy')

        return self._channels[self._current_channel]['name'], \
               False, \
               self._channels[self._current_channel]['current'], \
               0

    def _is_busy(self):
        return self._i2c.read_word(_I2C_ADDR, _I2C_REG_CONF) >> 15 == 0

    def _read_conversion(self):
        reg00 = self._i2c.read_word(_I2C_ADDR, _I2C_REG_CONV)

        # if self._logger.is_trace():
        #    ch_name = self._channels[self._current_channel]["name"]
        #    reg00_b = self._logger.to_bitstring(reg00)
        #    self._logger.trace(_LOG_PFX, f'read_conversion::ch={ch_name}, reg00={reg00} reg00_b={reg00_b} i2c_addr:{hex(_I2C_ADDR)}, i2c_reg_conv:{hex(_I2C_REG_CONV)}')

        reg00 = reg00 if reg00 < 32768 else reg00 - 65536

        # if self._logger.is_trace():
        #   self._logger.trace(_LOG_PFX, f'read_conversion::adjusted reg00={reg00}')

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
            if self._current_channel + 1 <= self._cfg_ch_max \
            else self._cfg_ch_min

        # if self._logger.is_trace():
        #    ch_name = self._channels[self._current_channel]["name"]
        #    self._logger.trace(_LOG_PFX, f'next_channel::ch={ch_name}')

    def _request_conversion(self):
        # if self._logger.is_trace():
        #    ch_name = self._channels[self._current_channel]["name"]
        #    ch_conf = self._logger.to_bitstring(self._channels[self._current_channel]["config"])
        #    self._logger.trace(_LOG_PFX, f'request_conversion::ch={ch_name}, ch_conf={ch_conf}, i2c_addr:{hex(_I2C_ADDR)}, i2c_reg_conf:{hex(_I2C_REG_CONF)}')

        self._i2c.write_word(_I2C_ADDR, _I2C_REG_CONF, self._channels[self._current_channel]['config'])

# https://www.ti.com/lit/ds/symlink/ads1115.pdf

# Address Pointer Register
#   7   6   5   4   3   2   1   0
#   0   0   0   0   0   0   0   0   conversion  0x00
#   0   0   0   0   0   0   0   1   config      0x01
#   0   0   0   0   0   0   1   0   lo_thresh   0x02
#   0   0   0   0   0   0   1   1   hi_thresh   0x03

# Conversion Register 0x00
#   15  14  13  12  11  10  9   8   7   6   5   4   3   2   1   0   16-bit conversion result

# Config Register 0x01
#   15  14  13  12  11  10  9   8   7   6   5   4   3   2   1   0
#
# --reading
#   operational status
#   0                                                               device busy
#   1                                                               device not busy
#
# --writing
#   conversion start
#   1                                                               start single conversion
#   input multiplexer
#       0   0   0                                                   ch0_ch1 (default)
#       1   0   0                                                   ch0_gnd
#       1   0   1                                                   ch1_gnd
#       1   1   0                                                   ch2_gnd
#       1   1   1                                                   ch3_gnd
#   gain amp
#                   0   0   1                                       pga_4.096v
#                   0   1   0                                       pga_2.048v (default)
#   operating mode
#                               0                                   continuous_conversion
#                               1                                   single_conversion (default)
#   data rate
#                                   1   1   1                       860_sps
#                                   1   0   0                       128_sps (default)
#                                   0   0   0                       8_sps
#   comparator mode
#                                               0                   traditional_comp (default)
#                                               1                   window_comp
#   comparator polarity
#                                                   0               active_low (default)
#                                                   1               active_high
#   latching comparator
#                                                       0           non_latch (default)
#                                                       1           latch
#   comparator queue
#                                                           0   0   assert_after_one
#                                                           0   1   assert_after_two
#                                                           1   0   assert_after_four
#                                                           1   1   disable (default)

# Operation
#   start conversion
#       i2c client_can_write word to 0x01 -> conversion start
#   check if conversion done
#       i2c read word config from 0x01
#           busy :      bit 15 = 0
#           not busy :  bit 15 = 1
#   i2c read word from 0x00 -> conversion result

# Example
#   start conversion for ch0_gnd, 4.096v, 860sps -> 0x01
#       0b1100001111100011  50147
#   0x01 -> check if done
#       0b1100001111100011  done
#   0x00 -> read result
#       0b1000011111000111  50147
#
#
#
#   start conversion for ch1_gnd, 4.096v, 860sps
#   0b1101001111100011  54243
#
#   read if busy
#   0b0000000000000000 >> 15  busy
#   0b1000000000000000 >> 15  not busy
