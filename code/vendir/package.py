"""
Functions for packaging.

TODO: Better doc string message as I was getting lazy on this one
"""

import sys
import subprocess

from vendir import config
CONFIG = config.ConfigSectionMap()


def pkg(root,
        version,
        output,
        identifier=CONFIG['pkgid'],
        install_location='/',
        sign=CONFIG['sign_cert_cn'],
        ownership='recommended'
        ):
    """
    Create a package.

    Most of the input parameters should be recognizable for most admins.
    `output` is the path so make sure and attach the pkg extension.

    Return:
      The exit code from pkgbuild. If non-zero an error has occurred
    """
    cmd = ['/usr/bin/pkgbuild', '--root', root,
           '--install-location', install_location,
           '--identifier', identifier,
           '--version', version,
           '--ownership', ownership]
    # When sign_cert_cn are passed we should sign the package
    if sign:
        cmd.append('--sign')
        cmd.append(sign)
    # Always append the output path so signing will work
    cmd.append(output)
    print(cmd)
    proc = subprocess.Popen(cmd, shell=False, bufsize=-1,
                            stdin=subprocess.PIPE,
                            stdout=sys.stdout, stderr=subprocess.PIPE)
    (output, dummy_error) = proc.communicate()
    return proc.returncode


if __name__ == '__main__':
    print 'This is a library of support tools'
