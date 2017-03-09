"""
Setup script to compile OpenSSL 1.0.2 for macOS
NOTE: OpenSSL 1.1 is not supported at this time due to large API changes.
      However OpenSSL version 1.0.2 is supported by the OpenSSL Software
      Foundation until 2019-12-31 (LTS).
"""

# standard libs
from distutils.dir_util import mkpath
from distutils.version import LooseVersion
import os
import shutil
import subprocess
import sys
import inspect
import tempfile
import argparse

# our libs. kind of hacky since this isn't a valid python package.
CURRENT_DIR = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PARENT_DIR)

from vendir import config  # noqa
from vendir import hash_helper  # noqa
from vendir import log  # noqa
from vendir import package  # noqa
from vendir import runner  # noqa


CONFIG = config.ConfigSectionMap()
OPENSSL_BUILD_DIR = os.path.abspath(CONFIG['openssl_build_dir'])
BASE_INSTALL_PATH = CONFIG['base_install_path']
BASE_INSTALL_PATH_S = CONFIG['base_install_path'].lstrip('/')
PKG_PAYLOAD_DIR = os.path.join(OPENSSL_BUILD_DIR, 'payload')
OPENSSL_VERSION = CONFIG['openssl_version']


def download_and_extract_openssl():
    """Download openssl distribution from the internet and extract it to
    openssl_build_dir."""
    if os.path.isdir(OPENSSL_BUILD_DIR):
        shutil.rmtree(OPENSSL_BUILD_DIR, ignore_errors=True)
    mkpath(OPENSSL_BUILD_DIR)
    # Download openssl
    log.info("Downloading OpenSSL from: {}".format(CONFIG['openssl_dist']))
    temp_filename = os.path.join(tempfile.mkdtemp(), 'tempdata')
    cmd = ['/usr/bin/curl', '--show-error', '--no-buffer',
           '--fail', '--progress-bar',
           '--speed-time', '30',
           '--location',
           '--url', CONFIG['openssl_dist'],
           '--output', temp_filename]
    # We are calling os.system so we can get download progress live
    rc = runner.system(cmd)
    if rc == 0 or rc is True:
        log.debug("OpenSSL download sucessful")
    else:
        log.error("OpenSSL download failed with exit code: '{}'".format(rc))
        sys.exit(1)

    # Verify openssl download hash
    download_hash = hash_helper.getsha256hash(temp_filename)
    config_hash = CONFIG['openssl_dist_hash']
    if download_hash != config_hash:
        log.error("Hash verification of OpenSSL download has failed. Download "
                  "hash of '{}' does not match config hash '{}'".format(
                    download_hash, config_hash))
        sys.exit(1)
    else:
        log.detail("Hash verification of OpenSSL sucessful")

    # Extract openssl to the openssl_build_dir
    log.info("Extracting OpenSSL...")
    cmd = ['/usr/bin/tar', '-xf', temp_filename, '-C', OPENSSL_BUILD_DIR,
           '--strip-components', '1']
    out = runner.Popen(cmd)
    if out[2] == 0:
        log.debug("Extraction completed sucessfully")
    else:
        log.error("Extraction has failed: {}".format(dummy_error))
    os.remove(temp_filename)


def build():
    """This is the main processing step that builds openssl from source"""
    # Step 1: change into our build directory
    os.chdir(OPENSSL_BUILD_DIR)
    # Don't compile openssl if the skip option is passed
    # Step 2: Run the Configure setup of OpenSSL to set correct paths
    openssl_install = os.path.join(BASE_INSTALL_PATH, 'openssl')
    log.info("Configuring OpenSSL...")
    cmd = ['./Configure',
           '--prefix={}'.format(openssl_install),
           '--openssldir={}'.format(openssl_install),
           'darwin64-x86_64-cc',
           'enable-ec_nistp_64_gcc_128',
           'no-ssl2',
           'no-ssl3',
           'no-zlib',
           'shared',
           'enable-cms',
           'no-comp',
           ]
    # OpenSSL 1.0 to 1.1 has some pretty major API and build differences.
    # Manage the build control with the following. NOTE: 1.1 is not
    # supported at this time. Hopefully in a future release.
    OLD_VERSION = None
    # OpenSSL renamed this build flag so was less confusing
    # https://github.com/openssl/openssl/commit/3c65577f1af1109beb8de06420efa09188981628
    TMP_DIR_FLAG = None
    if OPENSSL_VERSION > "1.1.0":
        OLD_VERSION = False
        TMP_DIR_FLAG = "DESTDIR"
    else:
        OLD_VERSION = True
        TMP_DIR_FLAG = "INSTALL_PREFIX"
    # If running 1.0 use runner.system() else runner.Popen()
    if OLD_VERSION:
        out = runner.system(cmd)
    else:
        out = runner.Popen(cmd)
    log.debug("Configuring returned value: {}".format(out))

    # Step 3: compile openssl. this will take a while.
    # FIXME: We need to check return codes.
    #        This command is required for OpenSSL lower than 1.1
    log.info("Compiling OpenSSL. This will take a while time...")
    if OLD_VERSION:
        log.detail("Running OpenSSL make depend routine...")
        cmd = ['/usr/bin/make', 'depend']
        proc = subprocess.Popen(cmd, bufsize=-1, stdout=sys.stdout)
        (output, dummy_error) = proc.communicate()
        sys.stdout.flush()  # does this help?

    log.detail("Running OpenSSL make routine...")
    cmd = ['/usr/bin/make']
    proc = subprocess.Popen(cmd, bufsize=-1, stdout=sys.stdout)
    (output, dummy_error) = proc.communicate()
    sys.stdout.flush()  # does this help?

    # log.detail("Running OpenSSL make test routine...")
    # cmd = ['/usr/bin/make', 'test']
    # proc = subprocess.Popen(cmd, bufsize=-1, stdout=sys.stdout)
    # (output, dummy_error) = proc.communicate()
    # sys.stdout.flush()  # does this help?

    mkpath(PKG_PAYLOAD_DIR)
    log.detail("Running OpenSSL make install routine...")
    cmd = ['/usr/bin/make',
           '{}={}'.format(TMP_DIR_FLAG, PKG_PAYLOAD_DIR),
           'install']
    print("ran a command: {}".format(' '.join(cmd)))
    out = runner.Popen(cmd, stdout=sys.stdout)
    sys.stdout.flush()  # does this help?


def post_install():
    """
    This helps work around a limitation with bundling your own version of
    OpenSSL. We copy the certs from Apple's 'SystemRootCertificates.keychain'
    into OPENSSL_BUILD_DIR/cert.pem
    https://goo.gl/s6vvwl
    """
    log.info("Writing the 'cert.pem' file from Apple's System Root Certs...")
    cmd = ['/usr/bin/security', 'find-certificate', '-a', '-p',
           '/System/Library/Keychains/SystemRootCertificates.keychain']
    out = runner.Popen(cmd)
    # Take the command output, out[0], and write the file to cert.pem
    cert_path = os.path.join(PKG_PAYLOAD_DIR, BASE_INSTALL_PATH_S,
                             'openssl', 'cert.pem')
    try:
        f = open(cert_path, "w")
        f.write(out[0])
        f.close()
    except(IOError) as e:
        log.error("Unable to write 'cert.pem': {}".format(e))


def main():
    """Main routine"""
    parser = argparse.ArgumentParser(prog='OpenSSL setup',
                                     description='This script will compile '
                                     'OpenSSL 1.0.1+ and optionally create '
                                     'a native macOS package.')
    parser.add_argument('-b', '--build', action='store_true',
                        help='Compile the OpenSSL binary')
    parser.add_argument('-s', '--skip', action='store_true',
                        help='Skip recompiling if possible. Only recommended '
                             'for development purposes.')
    parser.add_argument('-p', '--pkg', action='store_true',
                        help='Package the OpenSSL output directory.')
    parser.add_argument('-v', '--verbose', action='count', default=1,
                        help="Increase verbosity level. Repeatable up to "
                        "2 times (-vv)")
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()

    # set argument variables
    log.verbose = args.verbose
    skip = args.skip

    if args.build:
        log.info("Bulding OpenSSL...")
        check_dir = os.path.isdir(PKG_PAYLOAD_DIR)
        # When the skip option is passed and the build directory exists, skip
        # download and compiling of openssl. Note we still do linking.
        if (skip and check_dir):
            log.debug("Skip flag was provided. We will not compile OpenSSL "
                      "on this run.")
        else:
            download_and_extract_openssl()
            build()
            post_install()

    if args.pkg:
        log.info("Building a package for OpenSSL...")
        # Change back into our local directory so we can output our package
        # via relative paths
        os.chdir(CURRENT_DIR)
        version = CONFIG['openssl_version']
        rc = package.pkg(root=PKG_PAYLOAD_DIR,
                         version=version,
                         identifier="{}.openssl".format(CONFIG['pkgid']),
                         output='openssl-{}.pkg'.format(version),
                         )
        if rc == 0:
            log.info("OpenSSL packaged properly")
        else:
            log.error("Looks like package creation failed")


if __name__ == '__main__':
    main()
