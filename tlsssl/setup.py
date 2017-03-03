"""
Setup script to compile tlsssl to run againt python 2.7 or higher.
Has a dependency on openssl package being installed on this local machine
"""

# standard libs
from distutils.dir_util import mkpath
import os
import urllib2
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

# TODO: for when we make this into a package
# mkdir -p /Library/Python/2.7/site-packages/tlsssl
# cp build/lib.macosx-10.12-intel-2.7/{_tlsssl.so, tlsssl.py}
#       /Library/Python/2.7/site-packages/tlsssl
# mkdir -p /usr/local/lib/tlsssl
# cp build/lib.macosx-10.12-intel-2.7/{libtlscrypto.dylib, libtlsssl.dylib}
#       /usr/local/lib/tlsssl

# TODO: These need to come from CONFIG
# where an OpenSSL 1.0.1+ libssl.dylib and libcrypto.dylib are now
LIBS_SRC = "/usr/local/opt/openssl/lib"
# where you'll want them eventually installed
LIBS_DEST = "/usr/local/lib/tlsssl"
# where the associated headers are
HEADER_SRC = "/usr/local/opt/openssl/include"


def download_python_source_files():
    """Download CPython source files from Github. Verify the sha hash and
    redownload if they do not match."""
    src_dir = os.path.join(CURRENT_DIR, '_src')
    if not os.path.exists(src_dir):
        log.debug("Creating _src directory...")
        mkpath(src_dir)
    os.chdir(src_dir)
    gh_url = (
              'https://raw.githubusercontent.com/python/cpython/{}/'.format(
               CONFIG['cpython_2_7_git_commit'])
             )
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
                    log.warn("The file hash for '{}' does not match the "
                             "expected hash. It's hash is '{}'".format(
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
    patch_dir = os.path.join(CURRENT_DIR, '_patch')
    if not os.path.exists(patch_dir):
        log.debug("Creating _patch directory...")
        mkpath(patch_dir)
    patch_pairs = [
                   ['_patch/_tlsssl.c',           '_src/_ssl.c', ],
                   ['_patch/make_tlsssl_data.py', '_src/make_ssl_data.py'],
                   ['_patch/tlsssl.py',          '_src/ssl.py'],
                  ]
    log.info("Create our patched files...")
    for dest, source in patch_pairs:
        if not os.path.isfile(os.path.join(CURRENT_DIR, dest)):
            source = os.path.join(CURRENT_DIR, source)
            diff = os.path.join(CURRENT_DIR,
                                '_diffs',
                                "{}.diff".format(os.path.basename(dest)))
            dest = os.path.join(CURRENT_DIR, dest)
            log.debug("Patching '{}'".format(dest))
            _ = subprocess.check_output(['/usr/bin/patch',
                                         source,
                                         diff,
                                         "-o",
                                         dest])
    # Copy over the socketmodule.h file as well
    if not os.path.isfile(os.path.join(patch_dir, "socketmodule.h")):
        log.debug("Copying 'socketmodule.h' to the _patch dir")
        source = os.path.join(CURRENT_DIR, "_src", "socketmodule.h")
        shutil.copy(source, os.path.realpath(os.path.join(patch_dir)))


def build():
    """This is the main processing step that builds tlsssl from source"""
    # Step 1: make sure the _ssl_data.h header has been generated
    ssl_data = os.path.join(CURRENT_DIR, "_ssl_data.h")
    if not os.path.isfile(ssl_data):
        tool_path = os.path.join(CURRENT_DIR, "_patch", "make_tlsssl_data.py")
        # Run the generating script
        _ = subprocess.check_output(['/usr/bin/python',
                                    tool_path,
                                    HEADER_SRC,
                                    ssl_data])
    # Step 2: remove the temporary work directory under the build dir
    workspace_rel = os.path.join(self.build_temp, "../_temp_libs")
    workspace_abs = os.path.realpath(workspace_rel)
    shutil.rmtree(workspace_abs, ignore_errors=True)
    # Step 3: make the temporary work directory exist
    mkpath(workspace_rel)
    # Step 4: copy and rename the dylibs to there
    ssl_src = os.path.join(LIBS_SRC, "libssl.dylib")
    crypt_src = os.path.join(LIBS_SRC, "libcrypto.dylib")
    ssl_tmp = os.path.join(workspace_abs, "libtlsssl.dylib")
    crypt_tmp = os.path.join(workspace_abs, "libtlscrypto.dylib")
    shutil.copy(ssl_src, ssl_tmp)
    shutil.copy(crypt_src, crypt_tmp)
    # Step 5: change the ids of the dylibs
    ssl_dest = os.path.join(LIBS_DEST, "libtlsssl.dylib")
    crypt_dest = os.path.join(LIBS_DEST, "libtlscrypto.dylib")
    # (need to temporarily mark them as writeable)
    st = os.stat(ssl_tmp)
    os.chmod(ssl_tmp, st.st_mode | stat.S_IWUSR)
    st = os.stat(crypt_tmp)
    os.chmod(crypt_tmp, st.st_mode | stat.S_IWUSR)
    _ = subprocess.check_output(['/usr/bin/install_name_tool',
                                 '-id',
                                 ssl_dest,
                                 ssl_tmp])
    _ = subprocess.check_output(['/usr/bin/install_name_tool',
                                 '-id',
                                 crypt_dest,
                                 crypt_tmp])
    # Step 6: change the link between ssl and crypto
    # This part is a bit trickier - we need to take the existing entry
    # for libcrypto on libssl and remap it to the new location
    link_output = subprocess.check_output(['/usr/bin/otool',
                                           '-L',
                                           ssl_tmp])
    old_path = re.findall('^\t(/[^\(]+?libcrypto.*?.dylib)',
                          link_output,
                          re.MULTILINE)[0]
    _ = subprocess.check_output(['/usr/bin/install_name_tool',
                                 '-change',
                                 old_path,
                                 crypt_dest,
                                 ssl_tmp])
    # Step 7: cleanup permissions
    st = os.stat(ssl_tmp)
    os.chmod(ssl_tmp, st.st_mode & ~stat.S_IWUSR)
    st = os.stat(crypt_tmp)
    os.chmod(crypt_tmp, st.st_mode & ~stat.S_IWUSR)
    # Step 8: patch in the additional paths and linkages
    self.include_dirs.insert(0, HEADER_SRC)
    self.library_dirs.insert(0, workspace_abs)
    self.libraries.insert(0, "tlsssl")
    # # After we're done compiling, lets put the libs in with the build
    # # and clean up the temp directory
    # if not self.dry_run:
    #     # Step 1: clear out stale dylibs that may be in the final build dir
    #     ssl_build = os.path.join(self.build_lib, "libtlsssl.dylib")
    #     crypt_build = os.path.join(self.build_lib, "libtlscrypto.dylib")
    #     if os.path.isfile(ssl_build):
    #         os.remove(ssl_build)
    #     if os.path.isfile(crypt_build):
    #         os.remove(crypt_build)
    #     # Step 2: move the dylibs into the final build directory
    #     shutil.move(ssl_tmp, self.build_lib)
    #     shutil.move(crypt_tmp, self.build_lib)
    #     # Step 3: get rid of the temp lib directory
    #     shutil.rmtree(workspace_abs, ignore_errors=True)


def main():
    """Main routine"""
    parser = argparse.ArgumentParser(prog='tlsssl setup',
                                     description='This script will compile '
                                     'tlsssl and optionally create '
                                     'a native macOS package.')
    parser.add_argument('-b', '--build', action='store_true', required=True,
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
        download_python_source_files()
        patch()
        # build()

    if args.pkg:
        log.warn("Building a package for tlsssl is not supported yet")
        # log.info("Building a package for tlsssl...")
        # # Change back into our local directory so we can output our package
        # # via relative paths
        # os.chdir(CURRENT_DIR)
        # version = CONFIG['tlsssl_version']
        # rc = package.pkg(root=os.path.join(OPENSSL_BUILD_DIR, 'Library'),
        #                  version=version,
        #                  output='openssl.pkg'.format(version),
        #                  install_location='/Library',
        #                  )
        # if rc == 0:
        #     log.info("OpenSSL packaged properly")
        # else:
        #     log.error("Looks like Package creation failed")


if __name__ == '__main__':
    main()
