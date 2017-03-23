"""
Functions for hashing a file. This has been completely lifted from
Munki3.munkilib.munkihash
"""

import hashlib
import os


def gethash(filename, hash_function):
    """
    Calculates the hashvalue of the given file with the given hash_function.

    Args:
      filename: The file name to calculate the hash value of.
      hash_function: The hash function object to use, which was instantiated
          before calling this function, e.g. hashlib.md5().

    Returns:
      The hashvalue of the given file as hex string.
    """
    if not os.path.isfile(filename):
        return 'NOT A FILE'

    f = open(filename, 'rb')
    while 1:
        chunk = f.read(2**16)
        if not chunk:
            break
        hash_function.update(chunk)
    f.close()
    return hash_function.hexdigest()


def getsha256hash(filename):
    """
    Returns the SHA-256 hash value of a file as a hex string.
    """
    hash_function = hashlib.sha256()
    return gethash(filename, hash_function)


if __name__ == '__main__':
    print 'This is a library of support tools'
