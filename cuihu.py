#!/usr/bin/env python
from monitor import Monitor
import personal

secure_list = [71, 73,   76, 77, 78, 79,   84,85,86,87,88,89, ]
super_plan_a = [
    74,75,80,81,82,83,
]

super_plan_b = [
    92,93,98,99,100,101,
]

super_list = super_plan_a + super_plan_b

all = [71] + list(range(73, 89 + 1)) + [92,93,98,99,100,101]


if __name__ == '__main__':
    assert len(secure_list + super_list) == (len(secure_list) + len(super_list)) 
    assert set(secure_list + super_list) == set(all)

    m = Monitor(
        apikeys=personal.DEFAULT,
        enable_super=True,
        exclude=[],
        challenge_interval=45 * 60 * 1000,
        invalid_nodeids=[
            137764,  # s78n35
        ],

        only=all,

        ### plan a
        # ignore=super_plan_b + secure_list,

        ### plan b
        ignore=super_plan_a + secure_list,

        enable_manual_challenge=True,
        manual_challenge_duration=56 * 3600 * 1000,
        tolerance_interval=6 * 60 * 1000,
        cycle_interval=5 * 60 * 1000,
    )
    m.main_loop()
    

