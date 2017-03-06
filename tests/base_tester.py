# -*- coding: utf-8 -*-
"""
This is a utility script designed to allow you to run either py2 or py3 via:
    /some/path/to/python base_tester.py
in order to verify TLS 1.2 support and the version of openssl that python is
linked against.

The TEST_URL that we are using has TLSv1.2 enabled and SSLv2/SSLv3 disabled.
Since the stock OpenSSL (0.9.8zh) that ships with macOS is out of date the test
connection to a TLSv1.2 site will fail.
"""

# standard libs
from __future__ import print_function
import sys

# patched ssl using tlsssl
try:
    import tlsssl as ssl
    print("Using tlsssl")
except(ImportError):
    import ssl
    print("Using stock python ssl module")

PY_VER = sys.version_info
# TEST_URL = "https://developer.apple.com/"
TEST_URL = "https://fancyssl.hboeck.de/"

print("Our python is located: {}".format(sys.executable))
print("Our python version: {}.{}.{}".format(PY_VER[0], PY_VER[1], PY_VER[2]))
print("Our openssl is: {}".format(ssl.OPENSSL_VERSION))
print("------------------------------------------------------------------")

ctx = ssl.create_default_context()

if PY_VER[0] == 2:
    import urllib2
    try:
        a = urllib2.urlopen(TEST_URL, context=ctx)
        print("SUCCESS: Connection was made using TLS")
    except(urllib2.URLError) as e:
        print("ERROR: {}".format(e.reason))

if PY_VER[0] == 3:
    import urllib.request
    try:
        a = urllib.request.urlopen(TEST_URL, context=ctx)
        print(a)
        print("SUCCESS: Connection was made using TLS")
    except(ssl.SSLError, urllib.error.URLError) as e:
        print("ERROR: {}".format(e.reason))
