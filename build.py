#!/usr/bin/python
"""
build.py - main program for vendored
"""

import os
import sys
import subprocess
import argparse

from vendir import config

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def build_openssl(*args):
    """Build the openssl project."""
    openssl_dir = os.path.join(CURRENT_DIR, 'openssl')
    os.chdir(openssl_dir)
    cmd = ['/usr/bin/python', 'setup.py', '-vv', '-p', '-b', '-s']
    os.system(' '.join(cmd))


def build_python():
    """Build the python project."""
    openssl_dir = os.path.join(CURRENT_DIR, 'python')
    os.chdir(openssl_dir)
    cmd = ['/usr/bin/python', 'setup.py', '-vv', '-p', '-b']
    os.system(' '.join(cmd))


def build_tlsssl():
    """Build the tslssl project."""
    tslssl_dir = os.path.join(CURRENT_DIR, 'tlsssl')
    os.chdir(tslssl_dir)
    cmd = ['/usr/bin/python', 'setup.py', '-vv', '-p', '-b']
    os.system(' '.join(cmd))


def main():
    """Main routine"""
    build_openssl()
    build_python()
    build_tlsssl()


if __name__ == '__main__':
    main()
