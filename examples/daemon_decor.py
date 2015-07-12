#! /usr/bin/python3
from sys import argv
from os import getenv
from os.path import join
from dsm_pytools.daemon import daemon_decor
from time import sleep


fn = join(getenv('HOME'), 'daemon_example')
out = {'stdout': fn + '.log'}
action = None if len(argv) == 1 else argv[1]


@daemon_decor(fn + '.pid', **out)
def dmn_example(*arg):
    while True:
        print('testing daemon ...')
        sleep(5)


dmn_example(action)
