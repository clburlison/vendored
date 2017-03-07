"""
Setup script to compile Python for macOS, includes:
* PyObjC bridge
"""

# standard libs
from distutils.dir_util import mkpath
from distutils.version import LooseVersion
import os
import shutil
import sys
import inspect
import tempfile
import argparse
import urllib2

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
PYTHON_BUILD_DIR = os.path.abspath(CONFIG['python_build_dir'])
BASE_INSTALL_PATH = CONFIG['base_install_path']
BASE_INSTALL_PATH_S = CONFIG['base_install_path'].lstrip('/')
PKG_PAYLOAD_DIR = os.path.join(PYTHON_BUILD_DIR, 'payload')
PYTHON2_VERSION = CONFIG['python2_version']
SRC_DIR = os.path.join(CURRENT_DIR, '_src')
PATCH_DIR = os.path.join(CURRENT_DIR, '_patch')
PYTHON2_INSTALL = os.path.join(PYTHON_BUILD_DIR, 'payload',
                               BASE_INSTALL_PATH_S, 'Python', '2.7')
OPENSSL_INSTALL_PATH = os.path.join(CONFIG['base_install_path'], 'openssl')


def dl_and_extract_python():
    """Download Python distribution from the internet and extract it to
    PYTHON_BUILD_DIR."""
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
        log.debug("Python download sucessful")
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
        log.detail("Hash verification of Python sucessful")

    # Extract Python to the PYTHON_BUILD_DIR
    log.info("Extracting Python...")
    cmd = ['/usr/bin/tar', '-xf', temp_filename, '-C', PYTHON_BUILD_DIR,
           '--strip-components', '1']
    out = runner.Popen(cmd)
    if out[2] == 0:
        log.debug("Extraction completed sucessfully")
    else:
        log.error("Extraction has failed: {}".format(out[0]))
    os.remove(temp_filename)


def dl_apple_patch_files():
    """
    Download patches from Apple Opensource page.
    https://opensource.apple.com/source/python/python-97/2.7/fix/
    """
    log.info("Downloading and verifying python source files...")
    if not os.path.exists(SRC_DIR):
        log.debug("Creating _src directory...")
        mkpath(SRC_DIR)
    os.chdir(SRC_DIR)
    os_url = ('https://opensource.apple.com/source/python/python-97/2.7/fix/')
    configure_ed = (
        '3580144bc552fd9b70160b540b35af8ab18e15b592235e4c0731090c6dd98895')
    setup_py_ed = (
        '9db0803df2d816facf03b7879a5f6cca425b3e9513b60023323676d8c612d93d')
    readline_c_ed = (
        '96ff20308b223e22739f9942683bf8f36825e2bf0c426a2edcb6d741b56ff06f')
    setup_py_patch = (
        'c6bcd396cab445c3c7aed293720c7936ef773f0649849b658bba177046412f97')
    # This ugly looking block of code is a pair that matches the filename,
    # github url, and sha256 hash for each required python source file
    fp = [
      ['configure.ed', '{}configure.ed'.format(os_url), configure_ed],
      ['setup.py.ed', '{}setup.py.ed'.format(os_url), setup_py_ed],
      ['readline.c.ed', '{}readline.c.ed'.format(os_url), readline_c_ed],
      ['setup.py.patch', '{}setup.py.patch'.format(os_url), setup_py_patch],
    ]
    # Verify we have the correct python source files else download it
    log.detail("Downloading & checking hash of python patch files...")
    for fname, url, sha256 in fp:
        # This is a dual check step for file existence and hash matching
        log.debug("Checking source file: {}...".format(fname))
        if not os.path.isfile(fname) or (
                hash_helper.getsha256hash(fname) != sha256):
            log.info("Downloading '{}' source file...".format(fname))
            log.debug("Download url: {}".format(url))
            try:
                data = urllib2.urlopen(url)
                f = open(fname, "w")
                content = data.read()
                f.write(content)
                f.close()
                # Verify the hash of the source file we just downloaded
                download_file_hash = hash_helper.getsha256hash(fname)
                if download_file_hash != sha256:
                    log.warn("The hash for '{}' does not match the expected "
                             "hash. The downloaded hash is '{}'".format(
                              fname, download_file_hash))
                else:
                    log.debug("The download file '{}' matches our expected "
                              "hash of '{}'".format(fname, sha256))
            except(urllib2.HTTPError, urllib2.URLError,
                   OSError, IOError) as err:
                log.error("Unable to download '{}' "
                          "due to {}\n".format(fname, err))
                sys.exit(1)


def build(skip):
    """This is the main processing step that builds Python from source"""
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
        # Step 1.8: Run a few patches so we can compile cleanly
        dl_apple_patch_files()
        log.debug("Patching files into source...")
        cmd = ['/bin/ed', '-', os.path.join(PYTHON_BUILD_DIR, 'configure'), '<', os.path.join(SRC_DIR, 'configure.ed')]
        out = runner.Popen(cmd)
        runner.pprint(out)

        cmd = ['/bin/ed', '-', os.path.join(PYTHON_BUILD_DIR, 'setup.py'), '<', os.path.join(SRC_DIR, 'setup.py.ed')]
        out = runner.Popen(cmd)
        runner.pprint(out)

        cmd = ['/bin/ed', '-', os.path.join(PYTHON_BUILD_DIR, 'Modules/readline.c'), '<', os.path.join(SRC_DIR, 'readline.c.ed')]
        out = runner.Popen(cmd)
        runner.pprint(out)

        cmd = ['/usr/bin/patch', os.path.join(PYTHON_BUILD_DIR, 'setup.py'), os.path.join(SRC_DIR, 'setup.py.patch')]
        out = runner.Popen(cmd)
        runner.pprint(out)

        # Patch 2.7 SSL module. These shouldn't be needed as we're building
        # v2.7.13
        # cmd = ['/usr/bin/patch', os.path.join(PYTHON_BUILD_DIR, 'Modules/_hashopenssl.c'), os.path.join(PATCH_DIR, '_hashopenssl.c.patch')]
        # out = runner.Popen(cmd)
        # runner.pprint(out)
        #
        # cmd = ['/usr/bin/patch', os.path.join(PYTHON_BUILD_DIR, 'Modules/_ssl.c'), os.path.join(PATCH_DIR, '_ssl.c.patch')]
        # out = runner.Popen(cmd)
        # runner.pprint(out)
        #
        # cmd = ['/usr/bin/patch', os.path.join(PYTHON_BUILD_DIR, 'Lib/ssl.py'), os.path.join(PATCH_DIR, 'ssl.py.patch')]
        # out = runner.Popen(cmd)
        # runner.pprint(out)

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
        out = runner.Popen(cmd, stdout=sys.stdout)
        # Step 2.5: Patch files
        # FIXME: These patches fail and likely need to be recreated
        source = os.path.join(PYTHON_BUILD_DIR, 'Lib/ssl.py')
        patch = os.path.join(CURRENT_DIR, 'ssl.py.patch')
        cmd = ['/usr/bin/patch', source, patch]
        out = runner.Popen(cmd)
        runner.pprint(out)

        source = os.path.join(PYTHON_BUILD_DIR, 'Lib/logging/handlers.py')
        patch = os.path.join(CURRENT_DIR, 'handlers.py.patch')
        cmd = ['/usr/bin/patch', source, patch]
        out = runner.Popen(cmd)
        runner.pprint(out)
        # Step 3: compile Python. this will take a while.
        # FIXME: We need to check return codes.
        log.info("Compiling Python. This will take a while time...")
        log.detail("Running Python make routine...")
        cmd = ['/usr/bin/make']
        out = runner.Popen(cmd, stdout=sys.stdout)
        sys.stdout.flush()  # does this help?

        log.debug("Create some temp files thats")
        mkpath("/tmp/build-python/payload/Library/ITOps/Python/2.7/bin")
        log.detail("Running Python make install routine...")
        cmd = ['/usr/bin/make', 'install']
        out = runner.Popen(cmd, stdout=sys.stdout)
        sys.stdout.flush()  # does this help?
        # Step 4: Install PyOjbC bridge
        os.chdir(os.path.join(PYTHON2_INSTALL, 'bin'))
        # Update pip to latest
        log.info("Upgrading pip...")
        cmd = ['./pip', 'install', '--upgrade', 'pip']
        runner.Popen(cmd, stdout=sys.stdout)
        # Install a the specific version of PyObjc from config.ini
        log.info("Install PyObjC...")
        cmd = ['./python2.7', '-m', 'pip', 'install', '-U',
               'pyobjc=={}'.format(CONFIG['python2_objc_version'])]
        runner.Popen(cmd, stdout=sys.stdout)
        # os.system("./python2.7 -m pip install -U pyobjc-core")  # Not needed?

    else:
        log.info("Python compile skipped due to -skip option")


def main():
    """Main routine"""
    parser = argparse.ArgumentParser(prog='Python setup',
                                     description='This script will compile '
                                     'Python 1.0.1+ and optionally create '
                                     'a native macOS package.')
    parser.add_argument('-b', '--build', action='store_true', required=True,
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

    if args.build:
        log.info("Bulding Python...")
        check_dir = os.path.isdir(PKG_PAYLOAD_DIR)
        # When the skip option is passed and the build directory exists, skip
        # download and compiling of Python. Note we still do linking.
        if (skip and check_dir):
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
        rc = package.pkg(root=PKG_PAYLOAD_DIR,
                         version=PYTHON2_VERSION,
                         identifier="{}.python".format(CONFIG['pkgid']),
                         output='python-{}.pkg'.format(PYTHON2_VERSION),
                         )
        if rc == 0:
            log.info("Python packaged properly")
        else:
            log.error("Looks like package creation failed")


if __name__ == '__main__':
    main()
