#!/usr/bin/env python
from monitor import Monitor
import personal

if __name__ == '__main__':
    m = Monitor(
        apikeys=personal.MY,
        enable_super=True,
        only=list(range(301, 303 + 1)) + list(range(501, 502 + 1)),
        exclude=[],
        manual_challenge_duration=49 * 3600 * 1000,
    )
    m.main_loop()
    

