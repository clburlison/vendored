#!/usr/bin/python
"""
build.py - main program for vendored
"""

import os
import subprocess
from vendir import config

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def buildOpenSSL():
    """Build the openssl project locally and optionally package the binary."""
    openssl_dir = os.path.join(CURRENT_DIR, 'openssl')
    os.chdir(openssl_dir)
    print("Building openssl...")
    _ = subprocess.check_output(['make', 'build-pkg'])


def buildTslssl():
    """Build the tslssl project locally and optionally package the binary."""
    tslssl_dir = os.path.join(CURRENT_DIR, 'tlsssl')
    os.chdir(tslssl_dir)
    print("Building tslssl...")
    _ = subprocess.check_output(['python', 'setup.py', 'build'])


def main():
    """Main routine"""
    buildOpenSSL()
    buildTslssl()


if __name__ == '__main__':
    main()
