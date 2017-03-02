# Makefile for OpenSSL 1.1.0
# Latest package files should be gpg verified before use

include ../config.make
-include ../corp.make

PKGTITLE:=openssl
OPENSSL_BUILD:=/tmp/build-openssl

all: build-openssl build-pkg build-dmg

clean:
	/bin/rm -rf "${OPENSSL_BUILD}"
	/bin/rm -f ./openssl/openssl-*.{dmg,pkg}

#  THIS WAS AFTER THE `make -s depend` command
# sed -i.b -e "s%/tmp/the_luggage/openssl-[0-9]*/root%%" ./crypto/opensslconf.h \
# ./tools/c_rehash

build-openssl: clean
	/bin/mkdir "${OPENSSL_BUILD}"
	cd "${OPENSSL_BUILD}" && \
	curl -Lsf "${OPENSSL_DIST}" | tar -xzC "${OPENSSL_BUILD}" --strip-components=1 && \
	"${OPENSSL_BUILD}"/Configure \
		--prefix="${OPENSSL_BUILD}${BASE_INSTALL_PATH}/openssl" \
		--openssldir="${OPENSSL_BUILD}${BASE_INSTALL_PATH}/openssl" \
		no-ssl2 no-ssl3 no-idea no-zlib no-comp shared \
		darwin64-x86_64-cc enable-ec_nistp_64_gcc_128 && \
	make -s depend && \
	make -s all && \
	make install && \
	install_name_tool -id \
		"${BASE_INSTALL_PATH}/openssl/lib/libcrypto.1.1.dylib" \
		"${OPENSSL_BUILD}${BASE_INSTALL_PATH}/openssl/lib/libcrypto.1.1.dylib" && \
	install_name_tool -id \
		"${BASE_INSTALL_PATH}/openssl/lib/libssl.1.1.dylib" \
		"${OPENSSL_BUILD}${BASE_INSTALL_PATH}/openssl/lib/libssl.1.1.dylib" && \
	install_name_tool -change \
		"${OPENSSL_BUILD}${BASE_INSTALL_PATH}/openssl/lib/libssl.1.1.dylib" \
		"${BASE_INSTALL_PATH}/openssl/lib/libssl.1.1.dylib" \
		"${OPENSSL_BUILD}${BASE_INSTALL_PATH}/openssl/bin/openssl" && \
	install_name_tool -change \
		"${OPENSSL_BUILD}${BASE_INSTALL_PATH}/openssl/lib/libcrypto.1.1.dylib" \
		"${BASE_INSTALL_PATH}/openssl/lib/libcrypto.1.1.dylib" \
		"${OPENSSL_BUILD}${BASE_INSTALL_PATH}/openssl/bin/openssl" && \
	install_name_tool -change \
		"${OPENSSL_BUILD}${BASE_INSTALL_PATH}/openssl/lib/libssl.1.1.dylib" \
		"${BASE_INSTALL_PATH}/openssl/lib/libssl.1.1.dylib" \
		"${OPENSSL_BUILD}${BASE_INSTALL_PATH}/openssl/lib/libcrypto.1.1.dylib" && \
	install_name_tool -change \
		"${OPENSSL_BUILD}${BASE_INSTALL_PATH}/openssl/lib/libcrypto.1.1.dylib" \
		"${BASE_INSTALL_PATH}/openssl/lib/libcrypto.1.1.dylib" \
		"${OPENSSL_BUILD}${BASE_INSTALL_PATH}/openssl/lib/libssl.1.1.dylib"

build-pkg:
	pkgbuild --root "${OPENSSL_BUILD}/Library" --install-location "/Library" --identifier ${PKGID} ${PB_EXTRA_ARGS} --version ${OPENSSL_PKGVERSION} --ownership recommended ./${PKGTITLE}-${OPENSSL_PKGVERSION}.pkg

build-dmg:
	/usr/bin/hdiutil create -srcfolder ./${PKGTITLE}-${OPENSSL_PKGVERSION}.pkg -volname "${PKGTITLE}" -format UDZO -o ${PKGTITLE}-${OPENSSL_PKGVERSION}.dmg


.PHONY: all clean build-openssl build-pkg build-dmg
