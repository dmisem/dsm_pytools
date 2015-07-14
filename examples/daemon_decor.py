#! /usr/bin/python3
from sys import argv
from os import getenv
from os.path import join
from dsm_pytools.decor import daemon
from time import sleep


fn = join(getenv('HOME'), 'daemon_example')
out = {'stdout': fn + '.log'}
action = None if len(argv) == 1 else argv[1]


@daemon(fn + '.pid', **out)
def dmn_example():
    while True:
        print('testing daemon_decor ...')
        sleep(5)


dmn_example(action)
