"""Setup script to compile Python2 for macOS."""

# standard libs
from distutils.dir_util import mkpath
import os
import shutil
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
from vendir import root  # noqa


CONFIG = config.ConfigSectionMap()
PYTHON_BUILD_DIR = os.path.abspath(CONFIG['python_build_dir'])
BASE_INSTALL_PATH = CONFIG['base_install_path']
BASE_INSTALL_PATH_S = CONFIG['base_install_path'].lstrip('/')
PYTHON2_VERSION = CONFIG['python2_version']
PYTHON2_INSTALL = os.path.join(BASE_INSTALL_PATH, 'Python', '2.7')
OPENSSL_INSTALL_PATH = os.path.join(CONFIG['base_install_path'], 'openssl')


def dl_and_extract_python():
    """Download Python distribution and extract it to PYTHON_BUILD_DIR."""
    if os.path.isdir(PYTHON_BUILD_DIR):
        shutil.rmtree(PYTHON_BUILD_DIR, ignore_errors=True)
    mkpath(PYTHON_BUILD_DIR)
    # Download Python
    log.info("Downloading Python from: {}".format(CONFIG['python2_dist']))
    temp_filename = os.path.join(tempfile.mkdtemp(), 'tempdata')
    cmd = ['/usr/bin/curl', '--show-error', '--no-buffer',
           '--fail', '--progress-bar',
           '--speed-time', '30',
           '--location',
           '--url', CONFIG['python2_dist'],
           '--output', temp_filename]
    # We are calling os.system so we can get download progress live
    rc = runner.system(cmd)
    if rc == 0 or rc is True:
        log.debug("Python download successful")
    else:
        log.error("Python download failed with exit code: '{}'".format(rc))
        sys.exit(1)

    # Verify Python download hash
    download_hash = hash_helper.getsha256hash(temp_filename)
    config_hash = CONFIG['python2_dist_hash']
    if download_hash != config_hash:
        log.error("Hash verification of Python download has failed. Download "
                  "hash of '{}' does not match config hash '{}'".format(
                    download_hash, config_hash))
        sys.exit(1)
    else:
        log.detail("Hash verification of Python successful")

    # Extract Python to the PYTHON_BUILD_DIR
    log.info("Extracting Python...")
    cmd = ['/usr/bin/tar', '-xf', temp_filename, '-C', PYTHON_BUILD_DIR,
           '--strip-components', '1']
    out = runner.Popen(cmd)
    if out[2] == 0:
        log.debug("Extraction completed successfullyly")
    else:
        log.error("Extraction has failed: {}".format(out[0]))
    os.remove(temp_filename)


def build(skip):
    """Build custom Python2 from source."""
    # Step 1: change into our build directory
    os.chdir(PYTHON_BUILD_DIR)
    # Don't compile Python if the skip option is passed
    if not skip:
        # Step 1.5: Add extra modules
        setup_dist = os.path.join(PYTHON_BUILD_DIR, 'Modules/Setup.dist')
        with open(setup_dist, "a") as f:
            log.debug("Adding additional modules to be included...")
            f.write("_socket socketmodule.c timemodule.c\n")
            f.write("_ssl _ssl.c -DUSE_SSL "
                    "-I{0}/include -I{0}/include/openssl -L{0}/lib "
                    "-lssl -lcrypto".format(OPENSSL_INSTALL_PATH))
        # Step 2: Run the Configure setup of Python to set correct paths
        os.chdir(PYTHON_BUILD_DIR)
        if os.path.isdir(PYTHON2_INSTALL):
            shutil.rmtree(PYTHON2_INSTALL, ignore_errors=True)
        mkpath(PYTHON2_INSTALL)
        log.info("Configuring Python...")
        cmd = ['./configure',
               '--prefix={}'.format(PYTHON2_INSTALL),
               #    'CPPFLAGS=-I{}/include'.format(OPENSSL_INSTALL_PATH),
               #    'LDFLAGS=-L{}/lib'.format(OPENSSL_INSTALL_PATH),
               '--enable-shared',
               '--enable-toolbox-glue',
               '--with-ensurepip=install',
               '--enable-ipv6',
               '--with-threads',
               '--datarootdir={}/share'.format(PYTHON2_INSTALL),
               '--datadir={}/share'.format(PYTHON2_INSTALL),
               ]
        runner.Popen(cmd, stdout=sys.stdout)
        # Step 3: compile Python. this will take a while.

        # FIXME: We need to check return codes.
        log.info("Compiling Python. This will take a while time...")
        log.detail("Running Python make routine...")
        cmd = ['/usr/bin/make']
        runner.Popen(cmd, stdout=sys.stdout)
        sys.stdout.flush()  # does this help?

        log.debug("Create some temp files thats")
        log.detail("Running Python make install routine...")
        cmd = ['/usr/bin/make', 'install']
        runner.Popen(cmd, stdout=sys.stdout)
        sys.stdout.flush()  # does this help?
        # Step 4: Install pip + requirements
        os.chdir(os.path.join(PYTHON2_INSTALL, 'bin'))
        # Update pip to latest
        log.info("Upgrading pip...")
        cmd = ['./pip', 'install', '--upgrade', 'pip']
        runner.Popen(cmd, stdout=sys.stdout)
        # Install all pip modules from requirements.txt
        log.info("Install requirements...")
        requirements = os.path.join(CURRENT_DIR, 'requirements.txt')
        cmd = ['./python2.7', '-m', 'pip', 'install', '-r', requirements]
        runner.Popen(cmd, stdout=sys.stdout)
    else:
        log.info("Python compile skipped due to -skip option")


def main():
    """Build and package Python2."""
    parser = argparse.ArgumentParser(prog='Python setup',
                                     description='This script will compile '
                                     'Python 1.0.1+ and optionally create '
                                     'a native macOS package.')
    parser.add_argument('-b', '--build', action='store_true',
                        help='Compile the Python binary')
    parser.add_argument('-s', '--skip', action='store_true',
                        help='Skip recompiling if possible. Only recommended '
                             'for development purposes.')
    parser.add_argument('-p', '--pkg', action='store_true',
                        help='Package the Python output directory.')
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

    root.root_check()

    # Check for OpenSSL. If it isn't on disk in the proper location
    # we can't link against it.
    if not os.path.isdir(OPENSSL_INSTALL_PATH):
        log.warn("OpenSSL must be installed to '{}' prior to compiling "
                 "Python.".format(OPENSSL_INSTALL_PATH))
        sys.exit(1)

    if args.build:
        log.info("Bulding Python...")

        # When the skip option is passed and the build directory exists, skip
        # download and compiling of Python. Note we still do linking.
        if skip:
            log.debug("Skip flag was provided. We will not compile Python "
                      "on this run.")
        else:
            dl_and_extract_python()
            # reset trigger flag as we needed to download Python
            skip = False

        build(skip=skip)

    if args.pkg:
        log.info("Building a package for Python...")
        # Change back into our local directory so we can output our package
        # via relative paths
        os.chdir(CURRENT_DIR)
        rc = package.pkg(root=PYTHON2_INSTALL,
                         version=PYTHON2_VERSION,
                         identifier="{}.python".format(CONFIG['pkgid']),
                         install_location=PYTHON2_INSTALL,
                         output='python-{}.pkg'.format(PYTHON2_VERSION),
                         )
        if rc == 0:
            log.info("Python packaged properly")
        else:
            log.error("Looks like package creation failed")


if __name__ == '__main__':
    main()
