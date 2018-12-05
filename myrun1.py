#!/usr/bin/env python
# encoding=utf-8
from monitor import Monitor
import personal

my_own_list = [1, 399]

plan_a_securenode_list = list(range(301, 324 + 1))
plan_b_securenode_list = list(range(401, 424 + 1))

plan_a_supernode_list = list(range(501, 505 + 1))
plan_b_supernode_list = list(range(601, 605 + 1))

kl_a_securenode_list = list(range(1101, 1104 + 1))
kl_b_securenode_list = list(range(1201, 1206 + 1))

plan_a_ignore_list = my_own_list + plan_b_securenode_list + plan_b_supernode_list + kl_b_securenode_list

plan_b_ignore_list = my_own_list + plan_a_securenode_list + plan_a_supernode_list + kl_a_securenode_list


if __name__ == '__main__':
    m = Monitor(
        apikeys=personal.MY,
        enable_super=True,
        exclude=[],
        challenge_interval=42 * 60 * 1000,
        invalid_nodeids=[
            138052,138055,  # s407-1
            136345,         # s404-14
            131560,         # s321-16
        ],

        only=my_own_list + plan_a_securenode_list + plan_b_securenode_list + plan_a_supernode_list + plan_b_supernode_list + kl_a_securenode_list + kl_b_securenode_list,

        ###
        ### plan a
        ###
        # standard
        #ignore=my_own_list + plan_b_securenode_list + plan_b_supernode_list + kl_b_securenode_list,
        # other 过渡期
        #ignore=my_own_list + list(range(401, 500 + 1)) + list(range(601, 700 + 1)) + list(range(1101, 1102 + 1)) + kl_a_securenode_list + kl_b_securenode_list,
        #ignore=my_own_list + plan_b_securenode_list + plan_b_supernode_list + kl_a_securenode_list + kl_b_securenode_list,
        #ignore=my_own_list + plan_a_securenode_list + plan_b_securenode_list + plan_b_supernode_list + kl_a_securenode_list + kl_b_securenode_list,

        ###
        ### plan b
        ###
        # standard
        ignore=my_own_list + plan_a_securenode_list + plan_a_supernode_list + kl_a_securenode_list,
        #ignore=my_own_list + list(range(301, 400 + 1)) + list(range(501, 600 + 1)),
        #ignore=my_own_list + list(range(301, 400 + 1)) + list(range(501, 600 + 1)) + list(range(401, 424 + 1)),

        enable_manual_challenge=True,   # 在收割时，可以停止手动挑战

        manual_challenge_duration=55 * 3600 * 1000,
        tolerance_interval=6 * 60 * 1000,
        cycle_interval=5 * 60 * 1000,
    )
    m.main_loop()
    

