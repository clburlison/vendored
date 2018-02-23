#!/usr/bin/python
"""Build vendored packages."""

import os

from vendir import root

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def build_openssl(*args):
    """Build the openssl project."""
    openssl_dir = os.path.join(CURRENT_DIR, 'openssl')
    os.chdir(openssl_dir)
    cmd = ['/usr/bin/python', 'setup.py', '-vv', '-p', '-b', '-i']
    os.system(' '.join(cmd))


def build_python():
    """Build the python project."""
    openssl_dir = os.path.join(CURRENT_DIR, 'python')
    os.chdir(openssl_dir)
    cmd = ['/usr/bin/python', 'setup.py', '-vv', '-p', '-b']
    os.system(' '.join(cmd))


def build_tlsssl():
    """Build the tlsssl project."""
    tslssl_dir = os.path.join(CURRENT_DIR, 'tlsssl')
    os.chdir(tslssl_dir)
    cmd = ['/usr/bin/python', 'setup.py', '-vv', '-p', '-b']
    os.system(' '.join(cmd))


def main():
    """Build our required packages."""
    root.root_check()
    build_openssl()
    build_python()


if __name__ == '__main__':
    main()
