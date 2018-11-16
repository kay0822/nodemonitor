#!/usr/bin/env python
from monitor import Monitor
import personal

if __name__ == '__main__':
    m = Monitor(
        apikeys=personal.MY,
        enable_super=True,
        exclude=[],
        challenge_interval=45 * 60 * 1000,

        # plan a
        # only=list(range(501, 504 + 1)) + list(range(301, 318 + 1)) + list(range(413, 418 + 1)),
        # ignore=list(range(600, 700 + 1)) + list(range(401, 500 + 1)),

        # plan b
        #only=[399] + list(range(501, 504 + 1)) + list(range(301, 324 + 1)) + list(range(413, 424 + 1)),
        only=[399] + list(range(501, 505 + 1)) + list(range(301, 324 + 1)) + list(range(401, 406 + 1)) + list(range(413, 424 + 1)) + list(range(601, 605 + 1)),
        #ignore=list(range(313, 400 + 1)),
        ignore=[399] + list(range(401, 406 + 1)) + list(range(413, 500 + 1)) + list(range(601, 605 + 1)),
        # ignore=list(range(600, 700 + 1)) + list(range(401, 500 + 1)),

        #only=list(range(501, 504 + 1)) + list(range(301, 312 + 1)),
        #only=list(range(413, 424 + 1)),
        # other
        #only=list(range(501, 504 + 1)) + list(range(301, 313 + 1)) + list(range(315, 318 + 1)) + list(range(413, 418 + 1)),
        enable_manual_challenge=False,
        manual_challenge_duration=56 * 3600 * 1000,
        tolerance_interval=6 * 60 * 1000,
        cycle_interval=5 * 60 * 1000,
    )
    m.main_loop()
    

