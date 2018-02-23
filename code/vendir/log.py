"""
Functions for logging.

TODO: Update print statements to be py3 compatible
Borrowed heavily from Munki3.munkilib.munkilog & Munki3.munkilib.display

Useage:
    info("an info message here")        default level verbosity
    detail("A detail message here")     second level verbosity     -v
    debug("A debug message here")       third level verbosity      -vv
    warn("A warning message here")      default warning
    error("An error message here")      default error
"""

import sys
import warnings

verbose = None


def _to_unicode(obj, encoding='UTF-8'):
    """Coerces basestring obj to unicode."""
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj


def _concat_message(msg, *args):
    """Concatenate a string with any additional arguments.

    Returns:
        Unicode friendly string

    """
    # coerce msg to unicode if it's not already
    msg = _to_unicode(msg)
    if args:
        # coerce all args to unicode as well
        args = [_to_unicode(arg) for arg in args]
        try:
            msg = msg % tuple(args)
        except TypeError:
            warnings.warn(
                'String format does not match concat args: %s'
                % (str(sys.exc_info())))
    # if dealing with a string use rstrip()
    if isinstance(msg, basestring):
        return msg.rstrip()
    else:
        return msg


def info(msg, *args):
    """Display info messages."""
    msg = _concat_message(str(msg), *args)
    if verbose > 0:
        print '    %s' % msg.encode('UTF-8')
        sys.stdout.flush()


def detail(msg, *args):
    """
    Display minor info messages.

    These are usually logged only, but can be printed to
    stdout if verbose is set greater than 1
    """
    msg = _concat_message(str(msg), *args)
    if verbose > 1:
        print '    %s' % msg.encode('UTF-8')
        sys.stdout.flush()


def debug(msg, *args):
    """Display debug messages, formatting as needed."""
    msg = _concat_message(str(msg), *args)
    if verbose > 2:
        print '    %s' % msg.encode('UTF-8')
        sys.stdout.flush()


def warn(msg, *args):
    """Print warning msgs to stderr and the log."""
    msg = _concat_message(msg, *args)
    warning = 'WARNING: %s' % msg
    if verbose > 0:
        print >> sys.stderr, warning.encode('UTF-8')


def error(msg, *args):
    """Print msg to stderr and the log."""
    msg = _concat_message(msg, *args)
    errmsg = 'ERROR: %s' % msg
    if verbose > 0:
        print >> sys.stderr, errmsg.encode('UTF-8')


if __name__ == '__main__':
    print 'This is a library of support tools'
