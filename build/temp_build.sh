#!/bin/bash
# /usr/bin/productbuild --synthesize \
# --package ../openssl/openssl-1.0.2k.pkg \
# --package ../python/python-2.7.13.pkg \
# --package ../tlsssl/tlsssl-1.0.0.pkg \
# distribution.plist


/usr/bin/productbuild \
--distribution distribution.plist \
--resources resources \
--timestamp \
--sign "Developer ID Installer: Clayton Burlison (RP82Y2QL76)" \
vendored.pkg
