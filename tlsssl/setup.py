"""
Setup script to compile tlsssl to run againt python 2.7.
Has a dependency on openssl package being installed on this local machine.
"""

# standard libs
from distutils.dir_util import mkpath
from distutils.dir_util import copy_tree
import os
import urllib2
import shutil
import sys
import stat
import re
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
# where an OpenSSL 1.0.1+ libssl.dylib and libcrypto.dylib are now
LIBS_SRC = os.path.join(CONFIG['base_install_path'], 'openssl/lib')
# where you'll want them eventually installed
LIBS_DEST = os.path.join(CONFIG['tlsssl_install_dir'], 'lib')
# where the associated headers are
HEADER_SRC = os.path.join(CONFIG['base_install_path'], 'openssl/include')


def download_python_source_files():
    """Download CPython source files from Github. Verify the sha hash and
    redownload if they do not match."""
    log.info("Downloading and verifying python source files...")
    src_dir = os.path.join(CURRENT_DIR, '_src')
    if not os.path.exists(src_dir):
        log.debug("Creating _src directory...")
        mkpath(src_dir)
    os.chdir(src_dir)
    gh_url = 'https://raw.githubusercontent.com/python/cpython/v2.7.10/'
    # This ugly looking block of code is a pair that matches the filename,
    # github url, and sha256 hash for each required python source file
    fp = [
      ['ssl.py', '{}Lib/ssl.py'.format(gh_url), CONFIG['ssl_py_hash']],
      ['_ssl.c', '{}Modules/_ssl.c'.format(gh_url), CONFIG['ssl_c_hash']],
      ['make_ssl_data.py', '{}Tools/ssl/make_ssl_data.py'.format(gh_url),
       CONFIG['make_ssl_data_py_hash']],
      ['socketmodule.h',   '{}Modules/socketmodule.h'.format(gh_url),
       CONFIG['socketmodule_h_hash']],
    ]
    # Verify we have the correct python source files else download it
    log.detail("Downloading & checking hash of python source files...")
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
    # We are done with _src directory for now so go back to script root path
    os.chdir(CURRENT_DIR)


def patch():
    """This step creates are patch source files for usage in the build phase"""
    log.info("Creating our patch files for tlsssl...")
    patch_dir = os.path.join(CURRENT_DIR, '_patch')
    if not os.path.exists(patch_dir):
        log.debug("Creating _patch directory...")
        mkpath(patch_dir)
    patch_pairs = [
                   ['_patch/_tlsssl.c',           '_src/_ssl.c', ],
                   ['_patch/make_tlsssl_data.py', '_src/make_ssl_data.py'],
                   ['_patch/tlsssl.py',          '_src/ssl.py'],
                  ]
    log.detail("Create our patch files if they do not exist...")
    for dest, source in patch_pairs:
        if not os.path.isfile(os.path.join(CURRENT_DIR, dest)):
            source = os.path.join(CURRENT_DIR, source)
            diff = os.path.join(CURRENT_DIR,
                                '_diffs',
                                "{}.diff".format(os.path.basename(dest)))
            dest = os.path.join(CURRENT_DIR, dest)
            log.debug("Patching '{}'".format(dest))
            # TODO: Validate the return code and exist if something didn't work
            cmd = ['/usr/bin/patch', source, diff, "-o", dest]
            out = runner.Popen(cmd)
            runner.pprint(out)
    # Copy over the socketmodule.h file as well
    if not os.path.isfile(os.path.join(patch_dir, "socketmodule.h")):
        log.debug("Copying 'socketmodule.h' to the _patch dir")
        source = os.path.join(CURRENT_DIR, "_src", "socketmodule.h")
        shutil.copy(source, os.path.realpath(os.path.join(patch_dir)))

    log.detail("All patch files are created...")


def build():
    """This is the main processing step that builds tlsssl from source"""
    log.info("Building tlsssl...")
    patch_dir = os.path.join(CURRENT_DIR, '_patch')
    # Step 2: make sure the _ssl_data.h header has been generated
    ssl_data = os.path.join(patch_dir, "_ssl_data.h")
    if not os.path.isfile(ssl_data):
        log.debug("Generate _ssl_data.h header...")
        tool_path = os.path.join(CURRENT_DIR, "_patch", "make_tlsssl_data.py")
        # Run the generating script
        cmd = ['/usr/bin/python', tool_path, HEADER_SRC, ssl_data]
        out = runner.Popen(cmd)
        runner.pprint(out, 'debug')
    # Step 3: remove the temporary work directory under the build dir
    build_dir = os.path.join(CURRENT_DIR, 'build')
    if os.path.exists(build_dir):
        log.debug("Removing build directory...")
        shutil.rmtree(build_dir, ignore_errors=True)
    log.debug("Creating build directories...")
    mkpath(build_dir)
    # Step 3.5: copy tlsssl.py to the build directory
    log.info("Copy 'tlsssl.py' to the build directory...")
    shutil.copy(os.path.join(CURRENT_DIR, '_patch/tlsssl.py'), build_dir)
    workspace_rel = os.path.join(build_dir)
    workspace_abs = os.path.realpath(workspace_rel)
    # Step 4: copy and rename the dylibs to there
    log.detail("Copying dylibs to build directory")
    ssl_src = os.path.join(LIBS_SRC, "libssl.dylib")
    crypt_src = os.path.join(LIBS_SRC, "libcrypto.dylib")
    ssl_tmp = os.path.join(workspace_abs, "libtlsssl.dylib")
    crypt_tmp = os.path.join(workspace_abs, "libtlscrypto.dylib")
    try:
        shutil.copy(ssl_src, ssl_tmp)
        shutil.copy(crypt_src, crypt_tmp)
    except(IOError) as err:
        log.warn("tlsssl has a dependency on OpenSSL 1.0.1+ as such you "
                 "must build and install OpenSSL from ../openssl.")
        log.error("Build failed and will now exit!")
        log.error("{}".format(err))
        sys.exit(1)
    # Step 5: change the ids of the dylibs
    log.detail("Changing the ids of the dylibs...")
    ssl_dest = os.path.join(LIBS_DEST, "libtlsssl.dylib")
    crypt_dest = os.path.join(LIBS_DEST, "libtlscrypto.dylib")
    # (need to temporarily mark them as writeable)
    # NOTE: I don't think this I needed any longer
    st = os.stat(ssl_tmp)
    os.chmod(ssl_tmp, st.st_mode | stat.S_IWUSR)
    st = os.stat(crypt_tmp)
    os.chmod(crypt_tmp, st.st_mode | stat.S_IWUSR)

    cmd = ['/usr/bin/install_name_tool', '-id', ssl_dest, ssl_tmp]
    out = runner.Popen(cmd)
    runner.pprint(out, 'debug')

    cmd = ['/usr/bin/install_name_tool', '-id', crypt_dest, crypt_tmp]
    out = runner.Popen(cmd)
    runner.pprint(out, 'debug')

    # Step 6: change the link between ssl and crypto
    # This part is a bit trickier - we need to take the existing entry
    # for libcrypto on libssl and remap it to the new location
    cmd = ['/usr/bin/otool', '-L', ssl_tmp]
    out = runner.Popen(cmd)
    runner.pprint(out, 'debug')

    old_path = re.findall('^\t(/[^\(]+?libcrypto.*?.dylib)',
                          out[0],
                          re.MULTILINE)[0]
    log.debug("The old path was: {}".format(old_path))

    cmd = ['/usr/bin/install_name_tool', '-change', old_path, crypt_dest,
           ssl_tmp]
    out = runner.Popen(cmd)
    runner.pprint(out, 'debug')
    # Step 7: cleanup permissions
    # NOTE: Same. I don't think this I needed any longer
    st = os.stat(ssl_tmp)
    os.chmod(ssl_tmp, st.st_mode & ~stat.S_IWUSR)
    st = os.stat(crypt_tmp)
    os.chmod(crypt_tmp, st.st_mode & ~stat.S_IWUSR)
    # Step 8: patch in the additional paths and linkages
    # NOTE: This command will output a few warnings that are hidden at
    #       build time. Just an FYI in case this needs to be resolved in
    #       the future.
    system_python_path = ("/System/Library/Frameworks/Python.framework/"
                          "Versions/2.7/include/python2.7")
    cmd = ["cc", "-fno-strict-aliasing", "-fno-common", "-dynamic", "-arch",
           "x86_64", "-arch", "i386", "-g", "-Os", "-pipe", "-fno-common",
           "-fno-strict-aliasing", "-fwrapv", "-DENABLE_DTRACE", "-DMACOSX",
           "-DNDEBUG", "-Wall", "-Wstrict-prototypes", "-Wshorten-64-to-32",
           "-DNDEBUG", "-g", "-fwrapv", "-Os", "-Wall", "-Wstrict-prototypes",
           "-DENABLE_DTRACE", "-arch", "x86_64", "-arch", "i386", "-pipe",
           "-I{}".format(HEADER_SRC),
           "-I{}".format(system_python_path),
           "-c", "_patch/_tlsssl.c", "-o", "build/_tlsssl.o"]
    out = runner.Popen(cmd)
    if out[2] == 0:
        log.debug("Build of '_tlsssl.o' completed sucessfully")
    else:
        log.error("Build has failed: {}".format(out[1]))

    cmd = ["cc", "-bundle", "-undefined", "dynamic_lookup", "-arch",
           "x86_64", "-arch", "i386", "-Wl,-F.", "build/_tlsssl.o",
           "-L{}".format(workspace_abs), "-ltlsssl", "-ltlsssl", "-o",
           "build/_tlsssl.so"]
    out = runner.Popen(cmd)
    if out[2] == 0:
        log.debug("Build of '_tlsssl.so' completed sucessfully")
    else:
        log.error("Build has failed: {}".format(out[1]))

    log.debug("Remove temp '_tlsssl.o' from build directory")
    os.remove(os.path.join(build_dir, "_tlsssl.o"))


def main():
    """Main routine"""
    parser = argparse.ArgumentParser(prog='tlsssl setup',
                                     description='This script will compile '
                                     'tlsssl and optionally create '
                                     'a native macOS package.')
    parser.add_argument('-b', '--build', action='store_true',
                        help='Compile the tlsssl binaries')
    parser.add_argument('-p', '--pkg', action='store_true',
                        help='Package the tlsssl output directory.')
    parser.add_argument('-v', '--verbose', action='count', default=1,
                        help="Increase verbosity level. Repeatable up to "
                        "2 times (-vv)")
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)
    args = parser.parse_args()

    # set argument variables
    log.verbose = args.verbose

    if args.build:
        log.info("Bulding tslssl...")
        download_python_source_files()
        patch()
        build()

    if args.pkg:
        # FIXME: This has grown out of control. Move this outside of main!
        log.info("Building a package for tlsssl...")
        version = CONFIG['tlsssl_version']
        # we need to setup the payload
        payload_dir = os.path.join(CURRENT_DIR, 'payload')
        if os.path.exists(payload_dir):
            log.debug("Removing payload directory...")
            shutil.rmtree(payload_dir, ignore_errors=True)
        log.debug("Creating payload directory...")
        payload_lib_dir = os.path.join(payload_dir, LIBS_DEST.lstrip('/'))
        payload_root_dir = os.path.join(
            payload_dir, CONFIG['tlsssl_install_dir'].lstrip('/'))
        mkpath(payload_lib_dir)
        log.detail("Changing file permissions for 'tlsssl.py'...")
        # tlsssl.py needs to have chmod 644 so non-root users can import this
        os.chmod('build/tlsssl.py', stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        log.detail("Copying build files into payload directory")
        shutil.copy('build/_tlsssl.so', payload_root_dir)
        shutil.copy('build/tlsssl.py', payload_root_dir)
        shutil.copy('build/libtlscrypto.dylib', payload_lib_dir)
        shutil.copy('build/libtlsssl.dylib', payload_lib_dir)

        pth_fname = CONFIG['pth_fname']
        # if the pth_fname key is set write the .pth file
        if pth_fname is not '':
            log.debug("Write the '.pth' file so native python can read "
                      "this module without a sys.path.insert")
            python_sys = "/Library/Python/2.7/site-packages/"
            python_sys_local = os.path.join("payload", python_sys.lstrip('/'))
            log.debug("Make site-packages inside of payload")
            mkpath(python_sys_local)
            pth_file = os.path.join(python_sys_local, pth_fname)
            f = open(pth_file, 'w')
            f.write(os.path.dirname(LIBS_DEST))
            f.close()

        rc = package.pkg(root='payload',
                         version=version,
                         identifier="{}.tlsssl".format(CONFIG['pkgid']),
                         output='tlsssl-{}.pkg'.format(version),
                         )
        if rc == 0:
            log.info("tlsssl packaged properly")
        else:
            log.error("Looks like package creation failed")


if __name__ == '__main__':
    main()
