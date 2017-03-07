#!/bin/bash
# https://developer.apple.com/library/content/documentation/DeveloperTools/Reference/DistributionDefinitionRef/Chapters/Distribution_XML_Ref.html
# https://github.com/rust-lang/rust-packaging/blob/master/pkg/Distribution.xml
# https://github.com/saltstack/salt/tree/develop/pkg/osx


# /usr/bin/productbuild --synthesize \
# --package ./openssl-1.0.2j.pkg \
# --package ./python-2.7.10.pkg \
# distribution.plist


/usr/bin/productbuild \
--distribution distribution.plist \
--resources resources \
--timestamp \
--sign "Developer ID Installer: Clayton Burlison (RP82Y2QL76)" \
vendored.pkg
