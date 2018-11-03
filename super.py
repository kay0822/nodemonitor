#!/usr/bin/env python
from monitor import Monitor
import personal

if __name__ == '__main__':
    m = Monitor(
        apikeys=personal.MY_SUPER,
        enable_super=True,
        only=list(range(501, 504 + 1)),
        exclude=[],
        manual_challenge_duration=60 * 3600 * 1000,
        tolerance_interval=5 * 60 * 1000,
        cycle_interval=4 * 60 * 1000,
    )
    m.main_loop()
    

