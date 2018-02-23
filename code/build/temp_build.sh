#!/bin/bash
# /usr/bin/productbuild --synthesize \
# --package ../openssl/openssl-1.0.2n.pkg \
# --package ../python/python-2.7.14.pkg \
# --package ../tlsssl/tlsssl-1.1.0.pkg \
# distribution.plist


/usr/bin/productbuild \
--distribution distribution.plist \
--resources resources \
--timestamp \
--sign "Developer ID Installer: Clayton Burlison (RP82Y2QL76)" \
vendored.pkg
