# -*- coding: utf-8 -*-
"""
This is a utility script designed to allow you to run either py2 or py3 via:
    /some/path/to/python base_tester.py
in order to verify TLS version. You want TLS 1.2.
"""

# standard libs
from __future__ import print_function
import sys
import json

# patched ssl using tlsssl
try:
    import tlsssl as ssl
    print("Using tlsssl")
except(ImportError):
    import ssl
    print("Using stock python ssl module")

PY_VER = sys.version_info
# TEST_URL = "https://developer.apple.com/"
# TEST_URL = "https://fancyssl.hboeck.de/"
TEST_URL = "https://www.howsmyssl.com/a/check"

print("Our python is located: {}".format(sys.executable))
print("Our python version: {}.{}.{}".format(PY_VER[0], PY_VER[1], PY_VER[2]))
print("Our openssl is: {}".format(ssl.OPENSSL_VERSION))
print("------------------------------------------------------------------")

ctx = ssl.create_default_context()

if PY_VER[0] == 2:
    import urllib2
    try:
        a = urllib2.urlopen(TEST_URL, context=ctx)
        tls_ver = json.load(a)['tls_version']
        print("SUCCESS: Connection was made using {}".format(tls_ver))
    except(urllib2.URLError) as e:
        print("ERROR: {}".format(e.reason))

if PY_VER[0] == 3:
    import urllib.request
    try:
        a = urllib.request.urlopen(TEST_URL, context=ctx)
        tls_ver = json.load(a)['tls_version']
        print("SUCCESS: Connection was made using {}".format(tls_ver))
    except(ssl.SSLError, urllib.error.URLError) as e:
        print("ERROR: {}".format(e.reason))
