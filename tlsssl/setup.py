"""
Setup script to compile tlsssl to run againt python 2.7 or higher.
Has a dependency on openssl package being installed on this local machine
"""

from distutils.core import setup
from distutils.extension import Extension
from distutils.command.build_ext import build_ext
import urllib2
import os
import stat
import shutil
import subprocess
import re
import sys
import inspect

# Module level imports. This isn't a true python package so this looks hacky.
CURRENT_DIR = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, PARENT_DIR)

from vendir import config  # noqa
from vendir import hash_helper  # noqa

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


class custom_ext(build_ext):
    def run(self):
        if not self.dry_run:
            # Step 1: make sure the _ssl_data.h header has been generated
            ssl_data = os.path.join(CURRENT_DIR, "_ssl_data.h")
            if not os.path.isfile(ssl_data):
                tool_path = os.path.join(CURRENT_DIR, "make_tlsssl_data.py")
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
            self.mkpath(workspace_rel)
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
        result = build_ext.run(self)
        # After we're done compiling, lets put the libs in with the build
        # and clean up the temp directory
        if not self.dry_run:
            # Step 1: clear out stale dylibs that may be in the final build dir
            ssl_build = os.path.join(self.build_lib, "libtlsssl.dylib")
            crypt_build = os.path.join(self.build_lib, "libtlscrypto.dylib")
            if os.path.isfile(ssl_build):
                os.remove(ssl_build)
            if os.path.isfile(crypt_build):
                os.remove(crypt_build)
            # Step 2: move the dylibs into the final build directory
            shutil.move(ssl_tmp, self.build_lib)
            shutil.move(crypt_tmp, self.build_lib)
            # Step 3: get rid of the temp lib directory
            shutil.rmtree(workspace_abs, ignore_errors=True)
        return result


def download_python_source_files():
    """Download CPython source files from Github. Verify the sha hash and
    redownload if they do not match."""
    src_dir = os.path.join(CURRENT_DIR, '_src')
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
    should_bail = False
    for fname, url, sha256 in fp:
        # print(fname, url, sha256)
        if not os.path.isfile(fname) or (
                hash_helper.getsha256hash(fname) != sha256):
            print("Downloading '{}' source file...".format(fname))
            try:
                data = urllib2.urlopen(url)
                f = open(fname, "w")
                content = data.read()
                f.write(content)
                f.close()
            except(urllib2.HTTPError, urllib2.URLError,
                   OSError, IOError) as err:
                should_bail = TRUE
                sys.stderr.write("ERROR: Unable to download '{}' "
                                 "due to {}\n".format(fname, err))
    os.chdir(CURRENT_DIR)
    if should_bail:
        sys.exit()


def prep():
    """Prior to running setup, we should make our patched files if they
    don't exist"""
    patch_pairs = [
                   ['_tlsssl.c',           '_src/_ssl.c', ],
                   ['make_tlsssl_data.py', '_src/make_ssl_data.py'],
                   ['tlsssl.py',          '_src/ssl.py'],
                  ]
    for dest, source in patch_pairs:
        if not os.path.isfile(os.path.join(CURRENT_DIR, dest)):
            source = os.path.join(CURRENT_DIR, source)
            diff = os.path.join(CURRENT_DIR, '_diffs', "%s.diff" % dest)
            dest = os.path.join(CURRENT_DIR, dest)
            _ = subprocess.check_output(['/usr/bin/patch',
                                         source,
                                         diff,
                                         "-o",
                                         dest])
    # Copy over the socketmodule.h file as well
    if not os.path.isfile(os.path.join(CURRENT_DIR, "socketmodule.h")):
        source = os.path.join(CURRENT_DIR, "_src", "socketmodule.h")
        shutil.copy(source, os.path.realpath(os.path.join(CURRENT_DIR)))


download_python_source_files()

prep()

setup(
    name='tlsssl',
    description='TLS support backported into the macOS system python',
    url='https://github.com/pudquick/tlsssl',
    py_modules=['tlsssl'],
    ext_modules=[Extension("_tlsssl", ["_tlsssl.c"], libraries=["tlsssl"],)],
    cmdclass={'build_ext': custom_ext}
)
