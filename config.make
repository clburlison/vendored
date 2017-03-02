# The package idenitifer
PKGID:=com.example

# If you want to sign your package with a developer certificate. (OPTIONAL)
#    EX:  PB_EXTRA_ARGS+= --sign "Developer ID Installer: Clayton Burlison"
# PB_EXTRA_ARGS+=

# The base install directory
BASE_INSTALL_PATH:=/Library/ITOps

# Set OPENSSL_DIST to the location of your local downloaded copies
OPENSSL_DIST:=https://www.openssl.org/source/openssl-1.1.0e.tar.gz

# Version of OpenSSL that we are building
OPENSSL_PKGVERSION:=1.1.0
