#!/usr/bin/env python
from monitor import Monitor
import personal

if __name__ == '__main__':
    m = Monitor(
        apikeys=personal.MY,
        enable_super=True,
        exclude=[],
        # plan a
        # only=list(range(501, 504 + 1)) + list(range(301, 318 + 1)) + list(range(413, 418 + 1)),
        # ignore=list(range(600, 700 + 1)) + list(range(401, 500 + 1)),

        # plan b
        only=list(range(501, 504 + 1)) + list(range(301, 324 + 1)) + list(range(413, 424 + 1)),
        #only=list(range(501, 504 + 1)) + list(range(301, 304+1)) + list(range(306, 318 + 1)) + list(range(413, 424 + 1)),
        ignore=list(range(313, 400 + 1)),
        # ignore=list(range(600, 700 + 1)) + list(range(401, 500 + 1)),

        #only=list(range(501, 504 + 1)) + list(range(301, 312 + 1)),
        #only=list(range(413, 424 + 1)),
        # other
        #only=list(range(501, 504 + 1)) + list(range(301, 313 + 1)) + list(range(315, 318 + 1)) + list(range(413, 418 + 1)),
        manual_challenge_duration=60 * 3600 * 1000,
        tolerance_interval=6 * 60 * 1000,
        cycle_interval=5 * 60 * 1000,
    )
    m.main_loop()
    

