#!/usr/bin/env python
from monitor import Monitor

if __name__ == '__main__':
    m = Monitor(
        only=[1] + list(range(41, 43 + 1)) + list(range(46, 63 + 1)),
        exclude=[17, 18]
    )
    m.main_loop()
    

