"""
Wrapper functions for os.system and subprocess.Popen
"""

import subprocess
import os

from . import log


def pprint(data, level='debug'):
    """
    Pretty print our tuple return message from Popen method. The default level
    out output is 'debug' so we only display these messages on the maximum
    level of verbosity.
    """
    if level is 'info':
        log.detail(data[0])
        log.detail(data[1])
        log.detail(data[2])
    elif level is 'detail':
        log.debug(data[0])
        log.debug(data[1])
        log.debug(data[2])
    else:
        log.info(data[0])
        log.info(data[1])
        log.info(data[2])


def system(cmd):
    """
    Wrapper for os.system()

    Args:
      cmd: the command to run in list format

    Returns the exit code of the command
    """
    rc = os.WIFEXITED(os.system(' '.join(cmd)))
    return rc


def Popen(cmd, shell=False, bufsize=-1,
          stdin=subprocess.PIPE,
          stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    """
    Runner for subprocess.Popen()

    Args:
      these match the standard input arguments for subprocess.Popen

    Returns tuple of of the run in the order of:
      (output, error, returncode)
    """
    proc = subprocess.Popen(cmd, shell=shell, bufsize=bufsize,
                            stdin=stdin,
                            stdout=stdout, stderr=stderr)
    (output, error) = proc.communicate()
    # For values that are empty string convert them to None
    if output == '':
        output = None
    if error == '':
        error = None
    return (output, error, proc.returncode)


if __name__ == '__main__':
    print 'This is a library of support tools'
