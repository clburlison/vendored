"""
Setup script to compile OpenSSL 1.0.1+
"""

# standard libs
from distutils.dir_util import mkpath
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


CONFIG = config.ConfigSectionMap()
OPENSSL_BUILD_DIR = os.path.abspath(CONFIG['openssl_build_dir'])
BASE_INSTALL_PATH = CONFIG['base_install_path']
BASE_INSTALL_PATH_S = CONFIG['base_install_path'].lstrip('/')


def download_and_extract_openssl():
    """Download openssl distribution from the internet and extract it to
    openssl_build_dir."""
    if os.path.isdir(OPENSSL_BUILD_DIR):
        shutil.rmtree(OPENSSL_BUILD_DIR, ignore_errors=True)
    mkpath(OPENSSL_BUILD_DIR)
    # Download openssl
    log.info("Downloading OpenSSL...")
    temp_filename = os.path.join(tempfile.mkdtemp(), 'tempdata')
    cmd = ['/usr/bin/curl', '--show-error', '--no-buffer',
           '--fail', '--progress-bar',
           '--speed-time', '30',
           '--location',
           '--url', CONFIG['openssl_dist'],
           '--output', temp_filename]
    # We are calling os.system so we can get download progress live
    rc = os.WIFEXITED(os.system(' '.join(cmd)))
    if rc == 0 or rc is True:
        log.debug("OpenSSL download sucessful")
    else:
        log.error("OpenSSL download failed with exit code: '{}'".format(rc))
        sys.exit(1)

    # Verify openssl download hash
    # temp_filename = "/Users/clburlison/Downloads/openssl-1.1.0e.tar.gz"
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
    proc = subprocess.Popen(cmd, shell=False, bufsize=-1,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, dummy_error) = proc.communicate()
    if proc.returncode == 0:
        log.debug("Extraction completed sucessfully")
    else:
        log.error("Extraction has failed: {}".format(dummy_error))
    os.remove(temp_filename)


def build(skip):
    # Step 1: change into our build directory
    os.chdir(OPENSSL_BUILD_DIR)
    # Don't compile openssl if the skip option is passed
    if not skip:
        # Step 2: Run the Configure setup of OpenSSL to set correct paths
        openssl_tmp_dir = os.path.join(OPENSSL_BUILD_DIR,
                                       BASE_INSTALL_PATH_S, 'openssl')
        log.info("Configuring OpenSSL...")
        cmd = ['./Configure', '--prefix={}'.format(openssl_tmp_dir),
               '--openssldir={}'.format(openssl_tmp_dir), 'no-ssl3', 'no-idea',
               'no-zlib', 'no-comp', 'shared', 'darwin64-x86_64-cc',
               'enable-ec_nistp_64_gcc_128'
               ]
        proc = subprocess.Popen(cmd, shell=False, bufsize=-1,
                                stdin=subprocess.PIPE,
                                stdout=sys.stdout, stderr=subprocess.PIPE)
        (output, dummy_error) = proc.communicate()
        # Step 3: compile openssl. this will take a while.
        # FIXME: We need to check return codes.
        log.info("Compiling OpenSSL. This will take a while time...")
        log.detail("Running make depend routine...")
        cmd = ['/usr/bin/make', '-s', 'depend']  # no live output
        proc = subprocess.Popen(cmd, bufsize=-1, stdout=sys.stdout)
        (output, dummy_error) = proc.communicate()
        sys.stdout.flush()  # does this help?

        log.detail("Running make all routine...")
        cmd = ['/usr/bin/make', '-s', 'all']  # has live output
        proc = subprocess.Popen(cmd, bufsize=-1, stdout=sys.stdout)
        (output, dummy_error) = proc.communicate()
        sys.stdout.flush()  # does this help?

        log.detail("Running make install routine. "
                   "This command is the longest...")
        cmd = ['/usr/bin/make', 'install']  # has live output. LOTS of it.
        proc = subprocess.Popen(cmd, bufsize=-1, stdout=sys.stdout)
        (output, dummy_error) = proc.communicate()
        sys.stdout.flush()  # does this help?
    else:
        log.info("OpenSSL compile skipped due to -skip option")

    # Step 4: change the ids of the dylibs
    tmp_lib_dest = os.path.join(OPENSSL_BUILD_DIR, BASE_INSTALL_PATH_S,
                                'openssl', 'lib')
    tmp_bin_dest = os.path.join(OPENSSL_BUILD_DIR, BASE_INSTALL_PATH_S,
                                'openssl', 'bin')
    tgt_lib_dest = os.path.join(BASE_INSTALL_PATH,
                                'openssl', 'lib')

    # NOTE: These aren't using os.path.joins...it should be fine. Verify!
    log.info("Linking libraries and binaries to the correct path...")
    log.detail("Linking 1/6...")
    cmd = ['/usr/bin/install_name_tool', '-change',
           '{}/libcrypto.dylib'.format(tgt_lib_dest),
           '{}/libcrypto.dylib'.format(tmp_lib_dest)]
    proc = subprocess.Popen(cmd, shell=False, bufsize=-1,
                            stdin=subprocess.PIPE,
                            stdout=sys.stdout, stderr=subprocess.PIPE)
    (output, dummy_error) = proc.communicate()

    log.detail("Linking 2/6...")
    cmd = ['/usr/bin/install_name_tool', '-change',
           '{}/libssl.dylib'.format(tgt_lib_dest),
           '{}/libssl.dylib'.format(tmp_lib_dest)]
    proc = subprocess.Popen(cmd, shell=False, bufsize=-1,
                            stdin=subprocess.PIPE,
                            stdout=sys.stdout, stderr=subprocess.PIPE)
    (output, dummy_error) = proc.communicate()

    log.detail("Linking 3/6...")
    cmd = ['/usr/bin/install_name_tool', '-change',
           '{}/libssl.dylib'.format(tmp_lib_dest),
           '{}/libssl.dylib'.format(tgt_lib_dest),
           '{}/openssl'.format(tmp_bin_dest)]
    proc = subprocess.Popen(cmd, shell=False, bufsize=-1,
                            stdin=subprocess.PIPE,
                            stdout=sys.stdout, stderr=subprocess.PIPE)
    (output, dummy_error) = proc.communicate()

    log.detail("Linking 4/6...")
    cmd = ['/usr/bin/install_name_tool', '-change',
           '{}/libcrypto.dylib'.format(tmp_lib_dest),
           '{}/libcrypto.dylib'.format(tgt_lib_dest),
           '{}/openssl'.format(tmp_bin_dest)]
    proc = subprocess.Popen(cmd, shell=False, bufsize=-1,
                            stdin=subprocess.PIPE,
                            stdout=sys.stdout, stderr=subprocess.PIPE)
    (output, dummy_error) = proc.communicate()

    log.detail("Linking 5/6...")
    cmd = ['/usr/bin/install_name_tool', '-change',
           '{}/libssl.dylib'.format(tmp_lib_dest),
           '{}/libssl.dylib'.format(tgt_lib_dest),
           '{}/libcrypto.dylib'.format(tmp_lib_dest)]
    proc = subprocess.Popen(cmd, shell=False, bufsize=-1,
                            stdin=subprocess.PIPE,
                            stdout=sys.stdout, stderr=subprocess.PIPE)
    (output, dummy_error) = proc.communicate()

    log.detail("Linking 6/6...")
    cmd = ['/usr/bin/install_name_tool', '-change',
           '{}/libcrypto.dylib'.format(tmp_lib_dest),
           '{}/libcrypto.dylib'.format(tgt_lib_dest),
           '{}/libssl.dylib'.format(tmp_lib_dest)]
    proc = subprocess.Popen(cmd, shell=False, bufsize=-1,
                            stdin=subprocess.PIPE,
                            stdout=sys.stdout, stderr=subprocess.PIPE)
    (output, dummy_error) = proc.communicate()


def main():
    """Main routine"""
    parser = argparse.ArgumentParser(prog='OpenSSL setup',
                                     description='This script will compile '
                                     'OpenSSL 1.0.1+ and optionally create '
                                     'a native macOS package.')
    parser.add_argument('-b', '--build', action='store_true', required=True,
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
        check_dir = os.path.isdir(os.path.join(OPENSSL_BUILD_DIR,
                                  BASE_INSTALL_PATH_S,
                                  'openssl'))
        # When the skip option is passed and the build directory exists, skip
        # download and compiling of openssl. Note we still do linking.
        if not (skip and check_dir):
            download_and_extract_openssl()
            # reset trigger flag as we needed to download openssl
            skip = False
        build(skip=skip)

    if args.pkg:
        log.info("Building a package for OpenSSL...")
        # Change back into our local directory so we can output our package
        # via relative paths
        os.chdir(CURRENT_DIR)
        version = CONFIG['openssl_version']
        rc = package.pkg(root=os.path.join(OPENSSL_BUILD_DIR, 'Library'),
                         version=version,
                         output='openssl.pkg'.format(version),
                         install_location='/Library',
                         )
        if rc == 0:
            log.info("OpenSSL packaged properly")
        else:
            log.error("Looks like Package creation failed")


if __name__ == '__main__':
    main()
