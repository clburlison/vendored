# -*- coding: utf-8 -*-
"""
This is a utility script designed to allow you to run either py2 or py3 via:
    /some/path/to/python base_tester.py
in order to verify TLS 1.2 support and the version of openssl that python is
linked against.

Thank you to Hanno Böck for providing https://fancyssl.hboeck.de/ for free.
"""

# standard libs
from __future__ import print_function
import sys

# patched ssl using tlsssl
try:
    import tlsssl as ssl
except(ImportError):
    import ssl

PY_VER = sys.version_info

print("Our python is located: {}".format(sys.executable))
print("Our python version: {}.{}.{}".format(PY_VER[0], PY_VER[1], PY_VER[2]))
print("Our openssl is: {}".format(ssl.OPENSSL_VERSION))
print("------------------------------------------------------------------")

ctx = ssl.create_default_context()

if PY_VER[0] == 2:
    import urllib2
    try:
        a = urllib2.urlopen('https://fancyssl.hboeck.de/', context=ctx)
        print(a)
        print("SUCCESS: Connection was made using TLS1.2")
    except(urllib2.URLError) as e:
        print("ERROR: {}".format(e.reason))

if PY_VER[0] == 3:
    import urllib.request
    try:
        a = urllib.request.urlopen('https://fancyssl.hboeck.de/', context=ctx)
        print(a)
        print("SUCCESS: Connection was made using TLS1.2")
    except(ssl.SSLError, urllib.error.URLError) as e:
        print("ERROR: {}".format(e.reason))
