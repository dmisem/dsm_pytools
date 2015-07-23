"""
Daemonizing tools.
"""
import os
import sys
from time import sleep
from atexit import register
from signal import SIGTERM


_std = '/dev/null'


def daemon_exec(func, action, pidfile, stdin=_std, stdout=_std, stderr=_std):
    """ Implements daemon action ('start', 'stop', etc.) relative to func

    Arguments:
    func -- function object (infinite loop) to daemonize.
    action -- daemon action. See DMN_Actions for details.
    pidfile -- full name of file for keeping pid
    std -- dict with ('stdin', 'stdout', 'stderr') keys to redirect stream.
        Default is '/dev/null'
    """
    if action not in DMN_Actions:
        raise DMN_UnknownActionException(action)
    DMN_Actions[action](pidfile, func, stdin, stdout, stderr)


class Daemon:
    """
    A Class to  daemonizing function func.
    """
    def daemonize(self, pidfile, stdin, stdout, stderr):
        """
        do the UNIX double-fork magic,
        see Stevens' "Advanced Programming in the UNIX Environment"
        for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except(OSError) as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" %
                             (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except(OSError) as e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" %
                             (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(stdin, 'r')
        so = open(stdout, 'a+')
        se = open(stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        register(lambda: os.remove(pidfile))
        pid = str(os.getpid())
        open(pidfile, 'w+').write("%s\n" % pid)

    def start(self, pidfile, func, stdin=_std, stdout=_std, stderr=_std):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except(IOError):
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize(pidfile, stdin, stdout, stderr)
        func()

    def stop(self, pidfile, func=None, stdin=_std, stdout=_std, stderr=_std):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            with open(pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except(IOError):
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon is not running?\n"
            sys.stderr.write(message % pidfile)
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                sleep(0.1)
        except(OSError) as err:
            err = str(err)
            if ("No such process" in err) or ("Немає такого процесу" in err):
                if os.path.exists(pidfile):
                    os.remove(pidfile)
            else:
                print(err)
                sys.exit(1)

    def restart(self, pidfile, func, stdin=_std, stdout=_std, stderr=_std):
        """
        Restart the daemon
        """
        self.stop(pidfile)
        self.start(pidfile, func, stdin, stdout, stderr)


DMN_Actions = {
    'start': Daemon().start,
    'stop': Daemon().stop,
    'restart': Daemon().restart}


class DMN_UnknownActionException(Exception):
    """ Exception for wrong action """
    def __init__(self, action):
        self.action = action

    def __str__(self):
        s = "Unknown action '{0}'\n    Action should be in {1}"
        return s.format(self.action, tuple(DMN_Actions.keys()))
