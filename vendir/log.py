"""
Functions for logging
TODO: Update print statements to be py3 compatible
Borrowed heavily from Munki3 munkilib/munkilog & munkilib/display

Useage:
    info("an info message here")        default level verbosity
    detail("A detail message here")     second level verbosity     -v
    debug("A debug message here")       third level verbosity      -vv
    warn("A warning message here")      default warning
    error("An error message here")      default error
"""

import sys
import warnings


def _to_unicode(obj, encoding='UTF-8'):
    """Coerces basestring obj to unicode"""
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj


def _concat_message(msg, *args):
    """Concatenates a string with any additional arguments,
    making sure everything is unicode"""
    # coerce msg to unicode if it's not already
    msg = _to_unicode(msg)
    if args:
        # coerce all args to unicode as well
        args = [_to_unicode(arg) for arg in args]
        try:
            msg = msg % tuple(args)
        except TypeError, dummy_err:
            warnings.warn(
                'String format does not match concat args: %s'
                % (str(sys.exc_info())))
    return msg.rstrip()


def info(msg, *args):
    """
    Displays info messages.
    """
    msg = _concat_message(msg, *args)
    if verbose > 0:
        print '    %s' % msg.encode('UTF-8')
        sys.stdout.flush()


def detail(msg, *args):
    """
    Displays minor info messages.
    These are usually logged only, but can be printed to
    stdout if verbose is set greater than 1
    """
    msg = _concat_message(msg, *args)
    if verbose > 1:
        print '    %s' % msg.encode('UTF-8')
        sys.stdout.flush()


def debug(msg, *args):
    """
    Displays debug messages, formatting as needed.
    """
    msg = _concat_message(msg, *args)
    if verbose > 2:
        print '    %s' % msg.encode('UTF-8')
        sys.stdout.flush()


def warn(msg, *args):
    """
    Prints warning msgs to stderr and the log
    """
    msg = _concat_message(msg, *args)
    warning = 'WARNING: %s' % msg
    if verbose > 0:
        print >> sys.stderr, warning.encode('UTF-8')


def error(msg, *args):
    """
    Prints msg to stderr and the log
    """
    msg = _concat_message(msg, *args)
    errmsg = 'ERROR: %s' % msg
    if verbose > 0:
        print >> sys.stderr, errmsg.encode('UTF-8')


if __name__ == '__main__':
    print 'This is a library of support tools'
