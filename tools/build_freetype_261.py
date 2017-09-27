"""Build freetype 2.6.1 for tests.

On Unix systems, this script requires standard build tools (Autoconf) on the
PATH.  On Windows, this script requires 'cmake.exe' and 'nmake.exe' on the
PATH.
"""

from six.moves import urllib

from argparse import ArgumentParser
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile

import matplotlib


TESTS_FREETYPE_VERSION = "2.6.1"
TESTS_FREETYPE_HASH = '348e667d728c597360e4a87c16556597'
# NOTE: The patching algorithm is highly simplistic; see implementation.
CMAKELISTS_PATCH_REMOVE = [102, 103, 104]
CMAKELISTS_PATCH_ADD = [(309,
                         "set_target_properties(freetype "
                         "PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS TRUE)")]


def get_file_hash(filename):
    """Get the MD5 hash of a given file."""
    BLOCKSIZE = 1 << 16
    hasher = hashlib.md5()
    with open(filename, "rb") as fd:
        buf = fd.read(BLOCKSIZE)
        while buf:
            hasher.update(buf)
            buf = fd.read(BLOCKSIZE)
    return hasher.hexdigest()


def build_local_freetype():

    cache_dir = matplotlib.get_cachedir()
    tarball_name = "freetype-{}.tar.gz".format(TESTS_FREETYPE_VERSION)
    tarball_path = os.path.join(cache_dir, tarball_name)
    src_dir = os.path.join(
        cache_dir, "freetype-{}".format(TESTS_FREETYPE_VERSION))

    # Download.
    if (not os.path.isfile(tarball_path) or
            get_file_hash(tarball_path) != TESTS_FREETYPE_HASH):
        urls = [fmt.format(name=tarball_name,
                           version=TESTS_FREETYPE_VERSION)
                for fmt in ['https://downloads.sourceforge.net/project/'
                            'freetype/freetype2/{version}/{name}',
                            'https://download.savannah.gnu.org/releases/'
                            'freetype/{name}']]
        for url in urls:
            print("Downloading {}".format(url))
            try:
                urllib.request.urlretrieve(url, tarball_path)
            except IOError:  # URLError (a subclass) on Py3.
                print("Failed to download {}".format(url))
            else:
                if get_file_hash(tarball_path) != TESTS_FREETYPE_HASH:
                    print("Invalid hash")  # Could be a redirect.
                else:
                    break
        else:
            sys.exit("Failed to download freetype")

    # Build.
    shutil.rmtree(src_dir, ignore_errors=True)
    print("Building freetype from {}".format(tarball_path))

    if sys.platform.startswith("linux"):
        name = "libfreetype.so"
    elif sys.platform == "darwin":
        name = "libfreetype.dylib"
    elif sys.platform == "win32":
        name = "freetype.dll"
    else:
        raise ValueError("Unknown platform")

    with tarfile.open(tarball_path) as tar:
        tar.extractall(cache_dir)

    if sys.platform != "win32":
        env = os.environ.copy()
        env["CFLAGS"] = "{} -fPIC".format(env.get("CFLAGS", ""))
        subprocess.check_call(
            "./configure --with-zlib=no --with-bzip2=no --with-png=no "
            "--with-harfbuzz=no".split(), cwd=src_dir, env=env)
        subprocess.check_call("make", cwd=src_dir, env=env)

        shutil.copy(os.path.join(src_dir, "objs/.libs", name),
                    os.path.join(cache_dir, name))

    else:
        # The Windows build (including the patch) was copied from conda-forge.
        with open(os.path.join(src_dir, "CMakeLists.txt")) as file:
            cmakelists = file.readlines()
            for idx in CMAKELISTS_PATCH_REMOVE:
                cmakelists[idx] = ""  # Keep the indices.
            for idx, line in CMAKELISTS_PATCH_ADD:
                cmakelists.insert(idx, line)
        with open(os.path.join(src_dir, "CMakeLists.txt"), "w") as file:
            file.write("".join(cmakelists))
        build_dir = os.path.join(src_dir, "build")
        os.mkdir(build_dir)
        subprocess.check_call(
            'cmake.exe -G"NMake Makefiles" '
            '-DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS:Bool=true ..',
            cwd=build_dir)
        subprocess.check_call("nmake.exe", cwd=build_dir)

        shutil.copy(os.path.join(build_dir, name),
                    os.path.join(cache_dir, name))

    print("freetype library installed at {}."
          .format(os.path.join(cache_dir, name)))


if __name__ == "__main__":
    build_local_freetype()
