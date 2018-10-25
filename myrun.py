#!/usr/bin/env python
from monitor import Monitor
import personal

if __name__ == '__main__':
    m = Monitor(
        apikeys=personal.MY,
        enable_super=True,
        only=list(range(301, 306 + 1)) + list(range(501, 504 + 1)),
        exclude=[],
        manual_challenge_duration=49 * 3600 * 1000,
        tolerance_interval=9 * 60 * 1000,
        cycle_interval=6 * 60 * 1000,
    )
    m.main_loop()
    

