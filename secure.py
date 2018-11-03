#!/usr/bin/env python
from monitor import Monitor
import personal

if __name__ == '__main__':
    m = Monitor(
        apikeys=personal.MY_SECURE,
        enable_super=False,
        only=list(range(301, 315 + 1)),
        #only=list(range(307, 312 + 1)),
        exclude=[],
        manual_challenge_duration=60 * 3600 * 1000,
        tolerance_interval=8 * 60 * 1000,
        cycle_interval=5 * 60 * 1000,
    )
    m.main_loop()
    

