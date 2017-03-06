#!/usr/bin/python
"""
build.py - main program for vendored
"""

import os
import sys
import subprocess

from vendir import config

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def build_openssl():
    """Build the openssl project locally and optionally package the binary."""
    openssl_dir = os.path.join(CURRENT_DIR, 'openssl')
    os.chdir(openssl_dir)
    cmd = ['/usr/bin/python', 'setup.py', '-vv', '-p', '-b', '-s']
    os.system(' '.join(cmd))


def build_tlsssl():
    """Build the tslssl project locally and optionally package the binary."""
    tslssl_dir = os.path.join(CURRENT_DIR, 'tlsssl')
    os.chdir(tslssl_dir)
    cmd = ['/usr/bin/python', 'setup.py', '-vv', '-p', '-b']
    os.system(' '.join(cmd))


def main():
    """Main routine"""
    build_openssl()
    build_tlsssl()


if __name__ == '__main__':
    main()
