# Copyright (C) 2024, MRIIOT LLC
# All rights reserved.

import micropython
import gc
import utime


micropython.alloc_emergency_exception_buf(100)
gc.enable()

print('booting SHARC...')
# allow some time before starting main
utime.sleep(5)

gc.collect()
