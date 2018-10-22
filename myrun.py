#!/usr/bin/env python
from monitor import Monitor
import personal

if __name__ == '__main__':
    m = Monitor(
        apikeys=personal.MY,
        enable_super=True,
        only=[1] + list(range(31, 34 + 1)) + list(range(36, 55 + 1)),
        exclude=[17, 18]
    )
    m.main_loop()
    

