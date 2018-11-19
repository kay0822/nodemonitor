#!/usr/bin/env python
from monitor import Monitor
import personal

if __name__ == '__main__':
    m = Monitor(
        apikeys=personal.DEFAULT,
        enable_super=True,
        exclude=[],
        challenge_interval=45 * 60 * 1000,
        invalid_nodeids=[
            137764,  # s78n35
        ],

        # plan b
        only=[71] + list(range(73, 89 + 1)) + [92,93,98,99,100,101],
        ignore=[92,93,98,99,100,101],

        enable_manual_challenge=True,
        manual_challenge_duration=56 * 3600 * 1000,
        tolerance_interval=6 * 60 * 1000,
        cycle_interval=5 * 60 * 1000,
    )
    m.main_loop()
    

