#!/usr/bin/env python
from monitor import Monitor
import personal

if __name__ == '__main__':
    m = Monitor(
        apikeys=personal.MY,
        enable_super=True,
        exclude=[],
        challenge_interval=45 * 60 * 1000,
        invalid_nodeids=[
            138052,138055,  # s407-1
            136345,         # s404-14
            131560,         # s321-16
        ],

        only=[399] + list(range(301, 324 + 1)) + list(range(401, 424 + 1)) + list(range(501, 505 + 1)) + list(range(601, 605 + 1)),

        ### plan a
        #ignore=[399] + list(range(401, 500 + 1)) + list(range(601, 700 + 1)),

        ### plan b
        ignore=[399] + list(range(301, 400 + 1)) + list(range(501, 600 + 1)),

        enable_manual_challenge=True,
        manual_challenge_duration=56 * 3600 * 1000,
        tolerance_interval=6 * 60 * 1000,
        cycle_interval=5 * 60 * 1000,
    )
    m.main_loop()
    

