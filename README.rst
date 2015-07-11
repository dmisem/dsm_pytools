###########
dsm_pytools
###########
My collection of tools written in python3 or adapted to python3

Descriptions
============

.. contents::
   :depth: 1
   :backlinks: top

daemon.py
=========

Daemonizer for project

Usage example
-------------

.. code-block:: python

   from dsm_pytools.daemon import Daemon
   from time import sleep
   from sys import argv
   pidfile = '/home/dsm/test_daemon.pid'
   logfile = '/home/dsm/test_daemon.log'


   class MyProcess(Daemon):
       def run(self):
           while True:
               print('testing daemon ...')
               sleep(5)

   if len(argv) > 1:
       if argv[1] == 'start':
           MyProcess(pidfile, stdout=logfile).start()
       elif argv[1] == 'stop':
           MyProcess(pidfile, stdout=logfile).stop()
       elif argv[1] == 'restart':
           MyProcess(pidfile, stdout=logfile).restart()
       else:
           raise Exception('wrong argumens')
   else:
       raise Exception('nothin to do')
