from sys import exit, stderr, stdout, stdin
from time import sleep
import os
import time
import atexit
from signal import SIGTERM


def repeat_daemon_decor(sleep_time, pidfile, times=0, **std):

    def decor(func):

        def new_func():
            i = 1
            while (not times) or (i <= times):
                func()
                sleep(sleep_time)
                i += 1

        def act(action):
            res = daemon_exec(new_func, action, pidfile, **std)
            return res

        return act
    return decor


def daemon_decor(pidfile, **std):

    def decor(func):

        def act(action):
            res = daemon_exec(func, action, pidfile, **std)
            return res
        return act
    return decor


def daemon_exec(func, action, pidfile, **std):
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
        atexit.register(self.delpid)
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
            message = "pidfile %s does not exist. Daemon not running?\n"
            stderr.write(message % self.pidfile)
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except(OSError) as err:
            err = str(err)
            if err.find("No such process") > 0:
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
    def __init__(self, action):
        self.action = action

    def __str__(self):
        s = "Unknown action '{0}'\n    Action should be in {1}"
        return s.format(self.action, tuple(DMN_Actions.keys()))


def daemon_start(pidfile, func, **std):
    class DmnDecor(Daemon):
        def run(self):
            func()
    DmnDecor(pidfile, **std).start()


def daemon_stop(pidfile, func=None, **std):
    Daemon(pidfile, **std).stop()


def daemon_restart(pidfile, func, **std):
    class DmnDecor(Daemon):
        def run(self):
            func()
    DmnDecor(pidfile, **std).restart()


DMN_Actions = {
    'start': daemon_start,
    'stop': daemon_stop,
    'restart': daemon_restart}
