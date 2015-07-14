"""
Daemonizing tools.
"""
import os
from sys import exit, stderr, stdout, stdin
from time import sleep
from atexit import register
from signal import SIGTERM


def daemon_exec(func, action, pidfile, **std):
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
    DMN_Actions[action](pidfile, func, **std)


class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin='/dev/null',
                 stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
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
                exit(0)
        except(OSError) as e:
            stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            exit(1)

        # decouple from parent environment
        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                exit(0)
        except(OSError) as e:
            stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            exit(1)

        # redirect standard file descriptors
        stdout.flush()
        stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), stdin.fileno())
        os.dup2(so.fileno(), stdout.fileno())
        os.dup2(se.fileno(), stderr.fileno())

        # write pidfile
        register(self.delpid)
        pid = str(os.getpid())
        open(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except(IOError):
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            stderr.write(message % self.pidfile)
            exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            with open(self.pidfile, 'r') as pf:
                pid = int(pf.read().strip())
        except(IOError):
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon is not running?\n"
            stderr.write(message % self.pidfile)
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                sleep(0.1)
        except(OSError) as err:
            err = str(err)
            if ("No such process" in err) or ("Немає такого процесу" in err):
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(err)
                exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should override this method when you subclass Daemon.
        It will be called after the process has been
        daemonized by start() or restart().
        """


class DMN_UnknownActionException(Exception):
    """ Exception for wrong action """
    def __init__(self, action):
        self.action = action

    def __str__(self):
        s = "Unknown action '{0}'\n    Action should be in {1}"
        return s.format(self.action, tuple(DMN_Actions.keys()))


def _daemon_start(pidfile, func, **std):
    """ Starts func as daemon as write pif to pidfile"""
    class DmnDecor(Daemon):
        def run(self):
            func()
    DmnDecor(pidfile, **std).start()


def _daemon_stop(pidfile, func=None, **std):
    """ Stop daemon with pid from pidfile """
    Daemon(pidfile, **std).stop()


def _daemon_restart(pidfile, func, **std):
    """ Restart func as daemon with pid from pidfile """
    class DmnDecor(Daemon):
        def run(self):
            func()
    DmnDecor(pidfile, **std).restart()


DMN_Actions = {
    'start': _daemon_start,
    'stop': _daemon_stop,
    'restart': _daemon_restart}
