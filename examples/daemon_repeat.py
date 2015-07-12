#! /usr/bin/python3
from sys import argv
from os import getenv
from os.path import join
from dsm_pytools.daemon import repeat_daemon_decor as rdd


fn = join(getenv('HOME'), 'daemon_example')
out = {'stdout': fn + '.log'}
action = None if len(argv) == 1 else argv[1]


@rdd(5, fn + '.pid', **out)
def dmn_example():
    print('testing daemon ...')


dmn_example(action)
