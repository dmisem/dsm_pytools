"""
Daemonizing tools.
"""
import os
import sys
import signal
from time import sleep
from atexit import register


_std = '/dev/null'


def daemon_exec(func, action, pidfile, stdin=_std, stdout=_std, stderr=_std):
    """ Implements daemon action ('start', 'stop', etc.) relative to func

    Arguments:
    func -- function object (infinite loop) to daemonize.
    action -- daemon action. See DMN_Actions for details.
    pidfile -- full name of file for keeping pid
    std -- dict with ('stdin', 'stdout', 'stderr') keys to redirect stream.
        Default is '/dev/null'

    Simple doctest:
    >>> import os
    >>> import os.path as op
    >>> fn = op.join(os.getenv('HOME'), "daemon_exec_test.pid")
    >>> def func():
    ...    while True: sleep(10)
    ...
    >>> daemon_exec(func, 'test', fn)
    Traceback (most recent call last):
        ...
    DMN_UnknownActionException: Unknown action 'test'
        Action should be in ('restart', 'start', 'stop')
    >>> daemon_exec(func, 'start', fn)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    SystemExit: ...
    >>> sleep(0.1)
    >>> op.isfile(fn)
    True
    >>> daemon_exec(func, 'stop', fn)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    SystemExit: ...
    >>> sleep(0.1)
    >>> op.isfile(fn)
    False
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
        os.dup2(si.fileno(), 0)  # sys.stdin
        os.dup2(so.fileno(), 1)  # sys.stdout
        os.dup2(se.fileno(), 2)  # sys.stderr

        # write pidfile
        register(lambda: os.remove(pidfile))
        pid = str(os.getpid())
        with open(pidfile, 'w+') as f:
            f.write("%s\n" % pid)

    def start(self, pidfile, func, stdin=_std, stdout=_std, stderr=_std):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(pidfile, 'r') as pf:
                pid = int(pf.read().strip())
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % pidfile)
            sys.exit(1)
        except(IOError):
            pid = None

        # Start the daemon
        self.daemonize(pidfile, stdin, stdout, stderr)
        func()

    def stop(self, pidfile, func=None,
             stdin=_std, stdout=_std, stderr=_std,
             exit_on_error=True):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            with open(pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except(IOError):
            message = "pidfile %s does not exist. Daemon is not running?\n"
            sys.stderr.write(message % pidfile)
            if exit_on_error:
                sys.exit(1)
            else:
                return  # not an error in a restart

        # Try killing the daemon process
        try:
            os.kill(pid, signal.SIGTERM)
            sleep(0.1)
            os.kill(pid, signal.SIGHUP)
            sleep(0.1)
            os.kill(pid, signal.SIGKILL)
        finally:
            if os.path.isfile(pidfile):
                os.remove(pidfile)
            sys.exit(0)

    def restart(self, pidfile, func, stdin=_std, stdout=_std, stderr=_std):
        """
        Restart the daemon
        """
        self.stop(pidfile, exit_on_error=False)
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
        return s.format(self.action, tuple(sorted(DMN_Actions)))


if __name__ == "__main__":
    import doctest
    # doctest.testmod(raise_on_error=True)
    doctest.testmod()
