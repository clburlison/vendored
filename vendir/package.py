"""
Functions for packaging.
TODO: Better doc string message as I was getting lazy on this one
"""

import sys
import subprocess
import os

from vendir import config  # noqa
CONFIG = config.ConfigSectionMap()


def pkg(root,
        version,
        output,
        identifier=CONFIG['pkgid'],
        install_location='/',
        signing=CONFIG['pb_extra_args'],
        ownership='recommended'
        ):
    """
    Function to create a package. Most of the input parameters should be
    pretty reconizable for most admins. `output` is the path so make sure
    and attach the pkg extension.

    This function will return the exit code from the pkgbuild command. So if
    you don't get a zero something went wrong!
    """
    cmd = ['/usr/bin/pkgbuild', '--root', root,
           '--install-location', install_location,
           '--identifier', identifier,
           signing,
           '--version', version,
           '--ownership', ownership,
           output]
    # In case we aren't signing the page remove the empty element
    cmd.remove('')
    proc = subprocess.Popen(cmd, shell=False, bufsize=-1,
                            stdin=subprocess.PIPE,
                            stdout=sys.stdout, stderr=subprocess.PIPE)
    (output, dummy_error) = proc.communicate()
    return proc.returncode


if __name__ == '__main__':
    print 'This is a library of support tools'
