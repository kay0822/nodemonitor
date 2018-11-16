#!/usr/bin/env python
from monitor import Monitor

if __name__ == '__main__':
    m = Monitor(
        enable_super=True,
        only=list(range(41, 43 + 1)) + [46, 47, 48] + list(range(56, 79 + 1)) + list(range(80, 82)),
        exclude=[17, 18],
        tolerance_interval=8 * 60 * 1000,
        cycle_interval=5 * 60 * 1000,
    )
    m.main_loop()
    

