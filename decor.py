"""
Decorators kit
"""


from time import sleep
from dsm_pytools.daemon import daemon_exec as de


def repeat(sleep_time, times=0):
    """ Decorator for repeating function

    Arguments:
    sleep_time -- time interval in seconds
    times -- repeating times. If it is 0 use inrinite loop
    """

    def decor(func):

        def new_func():
            i = 1
            while (not times) or (i <= times):
                func()
                sleep(sleep_time)
        return new_func
    return decor


def repeat_daemon(sleep_time, pidfile, times=0, **std):
    """ Decorator for repeating and daemonizing function

    Arguments:
    sleep_time -- time interval in seconds
    pidfile -- file for daemon pid
    times -- repeating times. If it is 0 use inrinite loop
    std -- dict with ('stdin', 'stdout', 'stderr') keys to redirect std streams
        Default is '/dev/null'
    """

    def decor(func):
        def act(action):
            res = de(repeat(sleep_time, times)(func), action, pidfile, **std)
            return res

        return act
    return decor


def daemon(pidfile, **std):
    """ Decorator for daemonizing function

    Arguments:
    pidfile -- file for daemon pid
    std -- dict with ('stdin', 'stdout', 'stderr') keys to redirect std streams
        Default is '/dev/null'
    """

    def decor(func):

        def act(action):
            res = de(func, action, pidfile, **std)
            return res
        return act
    return decor
