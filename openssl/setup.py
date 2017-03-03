"""
Setup script to compile OpenSSL 1.0.1+
"""

# standard libs
from distutils.dir_util import mkpath
import urllib2
import os
import stat
import shutil
import subprocess
import re
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
    if not os.path.isdir(OPENSSL_BUILD_DIR):
        mkpath(OPENSSL_BUILD_DIR)
    # Download openssl
    log.info("Downloading OpenSSL...")
    temp_filename = os.path.join(tempfile.mkdtemp(), 'tempdata')
    f = open(temp_filename, 'wb')
    try:
        # Based off http://stackoverflow.com/a/2030027. Not in love with the
        # implementation.
        remote_file = urllib2.urlopen(CONFIG['openssl_dist'])
        try:
            total_size = remote_file.info().getheader('Content-Length').strip()
            header = True
        except AttributeError:
            # a response doesn't always include the "Content-Length" header
            header = False
        if header:
            total_size = int(total_size)
        bytes_so_far = 0
        chunk_size = 131072
        while True:
            buffer = remote_file.read(chunk_size)
            if not buffer:
                sys.stdout.write('\n')
                break

            bytes_so_far += len(buffer)
            f.write(buffer)
            if not header:
                total_size = bytes_so_far  # unknown size

            percent = float(bytes_so_far) / total_size
            percent = round(percent*100, 2)
            log.debug("Downloaded %d of %d bytes (%0.2f%%)\r" % (
                bytes_so_far, total_size, percent))
    except(urllib2.HTTPError, urllib2.URLError,
           OSError, IOError) as err:
        should_bail = True
        log.error("Unable to download 'OpenSSL' "
                  "due to {}\n".format(err))
        sys.exit(1)

    # Extract openssl to the openssl_build_dir
    log.info("Extracting OpenSSL...")
    cmd = ['/usr/bin/tar', '-xf', temp_filename, '-C', OPENSSL_BUILD_DIR,
           '--strip-components=1']
    proc = subprocess.Popen(cmd, shell=False, bufsize=-1,
                            stdin=subprocess.PIPE,
                            stdout=sys.stdout, stderr=subprocess.PIPE)
    (output, dummy_error) = proc.communicate()
    os.remove(temp_filename)


def build(skip):
    # Step 1: change into our build directory
    os.chdir(OPENSSL_BUILD_DIR)
    # Don't compile openssl if the output build dir exists and the skip option
    # is passed. Helpful for development purposes
    if not (skip and os.path.isdir(os.path.join(OPENSSL_BUILD_DIR,
                                                BASE_INSTALL_PATH_S,
                                                'openssl'))):
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
        # FIXME: This is really poorly done. I should check return codes.
        #        I was unable to get live output to stdout even with
        #        os.system(), so I might need help making this step better.
        log.info("Compiling OpenSSL. This will take a while time...")
        log.detail("Running make depend routine...")
        cmd = ['/usr/bin/make', '-s', 'depend']  # no live output
        os.system(' '.join(cmd))
        sys.stdout.flush()  # does this help?

        log.detail("Running make all routine...")
        cmd = ['/usr/bin/make', '-s', 'all']  # has live output
        os.system(' '.join(cmd))
        sys.stdout.flush()  # does this help?

        log.detail("Running make install routine. "
                   "This command is the longest...")
        cmd = ['/usr/bin/make', 'install']  # has live output. LOTS of it.
        os.system(' '.join(cmd))
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

    # set logging verbosity level
    log.verbose = args.verbose

    if args.build:
        download_and_extract_openssl()
        build(skip=args.skip)

    if args.pkg:
        log.info("Building a package for OpenSSL...")
        version = CONFIG['openssl_version']
        rc = package.pkg(root=os.path.join(OPENSSL_BUILD_DIR, 'Library'),
                         version=version,
                         output='openssl.pkg'.format(version),
                         install_location='/Library',
                         )
        if rc is not 0:
            log.error("Looks like Package creation failed")
        else:
            log.info("OpenSSL packaged properly")


if __name__ == '__main__':
    main()
