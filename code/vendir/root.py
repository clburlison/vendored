"""Check for root."""

import sys
import os


def root_check():
    """Check for root access."""
    if not os.geteuid() == 0:
        sys.stderr.write("You must run this as root!")
        exit(1)


if __name__ == '__main__':
    print 'This is a library of support tools'
