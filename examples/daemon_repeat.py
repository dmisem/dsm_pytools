#! /usr/bin/python3
from sys import argv
from os import getenv
from os.path import join
from dsm_pytools.decor import repeat_daemon as rd


fn = join(getenv('HOME'), 'daemon_example')
out = {'stdout': fn + '.log'}
action = None if len(argv) == 1 else argv[1]


@rd(5, fn + '.pid', **out)
def dmn_example():
    print('testing daemon_repeat ...')


dmn_example(action)
