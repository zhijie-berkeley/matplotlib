"""Setup configuration for Matplotlib.
"""

from __future__ import print_function, absolute_import

from distutils.version import LooseVersion
import glob
import os
import shlex
import shutil
from string import Template
import subprocess
import sys
import sysconfig
import tempfile

if sys.version_info < (3,):
    from ConfigParser import SafeConfigParser as ConfigParser
else:
    from configparser import ConfigParser

import setuptools
from setuptools import Extension

import _setupext_backports as _backports


class SetupExtError(Exception):
    """Base class for exceptions that should be caught and handled."""


class SetupCfgError(SetupExtError):
    """Exception thrown for invalid entries in setup.cfg."""


class PkgConfigError(SetupExtError):
    """Exception thrown when pkg-config fails to find a dependency."""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return ("Could not find headers for {}.  Try installing with conda or "
                "your distribution's package manager.".format(self.name))


def _load_setup_cfg():
    options = {
        "backend": None,
        "display_status": True,
    }
    path = os.environ.get("MPLSETUPCFG", "setup.cfg")
    config = ConfigParser()
    try:
        config.read(path)
    except IOError:
        pass
    if config.has_option("rc_options", "backend"):
        options["backend"] = config.get("rc_options", "backend")
    if config.has_option("directories", "basedirlist"):
        options["basedirlist"] = [
            x.strip() for x in
            config.get("directories", "basedirlist").split(",")]
    if config.has_option("status", "suppress"):
        options["display_status"] = not config.getboolean("status", "suppress")
    return config, options


_CONFIG, OPTIONS = _load_setup_cfg()
log = print if OPTIONS["display_status"] else lambda *args, **kwargs: None


def get_config(category, name, default):
    """Return the boolean configuration set in setup.cfg ("auto", True, False).
    """
    if not _CONFIG.has_option(category, name):
        return default
    try:
        return _CONFIG.getboolean(category, name)
    except ValueError:
        if _CONFIG.get(category, name) == "auto":
            return default
        else:
            raise


def get_enum_config(category, name, choices):
    """Return the configuration set in setup.cfg.

    It must be one of the values listed in choices, and defaults to the first
    value if not set.  Otherwise, a ValueError is raised.
    """
    if _CONFIG.has_option(category, name):
        value = _CONFIG.get(category, name)
        if value in choices:
            return value
        else:
            raise SetupCfgError(
                "Invalid setup.cfg entry: {}.{} should be one of {}".format())
    else:
        return choices[0]


if sys.platform == "win32":
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        if "CL" not in os.environ:
            os.environ["CL"] = ""
        os.environ["CL"] += ' /I"{}" /I"{}"'.format(
            os.path.join(conda_prefix, "Library", "include"),
            # A bit hackish, but seems easier than adding more logic...
            os.path.join(conda_prefix, "Library", "include", "freetype2"))
        if "LINK" not in os.environ:
            os.environ["LINK"] = ""
        os.environ["LINK"] += ' /LIBPATH:"{}"'.format(
            os.path.join(conda_prefix, "Library", "lib"))


class Package(object):
    """A build dependency.
    """

    # If the dependency is optional and will, in fact, not be built, unset the
    # `.built` attribute (in that case, the subsequent attributes will not be
    # used).  Compulsory dependencies which cannot be built should instead
    # throw a PkgConfigError if they cannot be built.
    built = True

    # If the dependency provides a backend, set the `.provides_backend`
    # attribute accordingly.  This is used to compute the default backend.
    provides_backend = None

    # The following attributes are merged into the kwargs passed to `setup()`.
    install_requires = []
    extras_require = {}
    packages = []
    namespace_packages = []
    py_modules = []
    ext_modules = []
    package_data = {}

    @staticmethod
    def add_flags(ext):
        """
        Modify an `Extension`'s build flags which has this class as dependency.
        """
        raise NotImplementedError

    @classmethod
    def register(cls, setup_kwargs):
        """
        Add this class (if built) to the kwargs ultimately passed to setup.
        """
        if not cls.built:
            return
        setup_kwargs["install_requires"].extend(cls.install_requires)
        for key, value in cls.extras_require.items():
            setup_kwargs["extras_require"].setdefault(key, []).extend(value)
        setup_kwargs["packages"].extend(cls.packages)
        setup_kwargs["namespace_packages"].extend(cls.namespace_packages)
        setup_kwargs["py_modules"].extend(cls.py_modules)
        setup_kwargs["ext_modules"].extend(cls.ext_modules)
        for key, value in cls.package_data.items():
            setup_kwargs["package_data"].setdefault(key, []).extend(value)


def process_packages(packages, setup_kwargs):
    max_len = max(len(pkg.__name__) for pkg in packages)
    default_backend = "agg"
    for pkg in packages:
        log("{:>{}}: {}".format(pkg.__name__, max_len,
                                {True: "yes", False: "no"}[pkg.built]))
        pkg.register(setup_kwargs)
        if pkg.built and pkg.provides_backend:
            default_backend = pkg.provides_backend
    if OPTIONS["backend"] is not None:
        default_backend = OPTIONS["backend"]
    with open("matplotlibrc.template") as file:
        template = file.read()
    template = Template(template)
    with open("lib/matplotlib/mpl-data/matplotlibrc", "w") as file:
        file.write(template.safe_substitute(TEMPLATE_BACKEND=default_backend))
    return setup_kwargs


class delayed_str(object):
    """A class whose `__str__` is computed by calling a given function.

    This is a hack used to add `np.get_include` to the include path of
    extensions, but only call the function after numpy has been installed.
    """

    def __init__(self, func):
        self._func = func

    def __str__(self):
        return self._func()


def with_dependencies(ext, deps):
    """
    Modify an `Extension` by adding the build flags for the given dependencies.
    """
    for dep in deps:
        try:
            dep.add_flags(ext)
        except SetupExtError as exc:
            sys.exit(str(exc))
    ext.include_dirs.append(".")
    return ext


class _PkgConfig(object):
    """A singleton class used to communicate with pkg-config.
    """

    def __init__(self):
        executable = os.environ.get("PKG_CONFIG", None) or "pkg-config"
        if _backports.which(executable):
            self._executable = executable
            pkgconfig_path = sysconfig.get_config_var("LIBDIR")
            if pkgconfig_path is None:
                return
            pkgconfig_path = os.path.join(pkgconfig_path, "pkgconfig")
            if not os.path.isdir(pkgconfig_path):
                return
            try:
                os.environ["PKG_CONFIG_PATH"] += ":" + pkgconfig_path
            except KeyError:
                os.environ["PKG_CONFIG_PATH"] = pkgconfig_path
        else:
            log("WARNING: pkg-config is not installed; Matplotlib may be "
                "unable to find some dependencies.")
            self._executable = None
        self._header_cache = {}

    def add_flags(self, ext, name, min_version=None, alt_exec=None,
                  fallback_header=None, fallback_name=None):
        """Add pkg-config flags to an `Extension`.

        Parameters
        ----------
        ext : Extension
            The extension that needs the dependency.
        name : str
            Name of the library for pkg-config.
        min_version : str, optional
            If set, the minimal version, as returned by
            ``pkg-config --modversion $name`` or ``$alt_exec --version``.
        alt_version : str, optional
            If set, a pkg-config-like executable which will be called instead
            of pkg-config if it exists.
        fallback_header : str, optional
            If set, path to a header file; if the header file is found by the
            compiler when building an otherwise empty extension module, the
            dependency is considered satisfied even if there is no pkg-config
            information available.
        fallback_name : str, optional
            If the library was found via *fallback_header*, the library name is
            set to *fallback_name* if it is set; otherwise, the pkg-config name
            is used.
        """
        try:
            if alt_exec is not None and _backports.which(alt_exec):
                def get_output(flag):
                    # Py2.7 workaround.
                    with open(os.devnull, "w") as devnull:
                        return shlex.split(subprocess.check_output(
                            [alt_exec, flag],
                            universal_newlines=True, stderr=devnull))
                version, = get_output("--version")
            elif self._executable:
                def get_output(flag):
                    # Py2.7 workaround.
                    with open(os.devnull, "w") as devnull:
                        return shlex.split(subprocess.check_output(
                            [self._executable, flag, name],
                            universal_newlines=True, stderr=devnull))
                version, = get_output("--modversion")
            else:
                return self._check_fallback_header(
                    ext, name, fallback_header, fallback_name)
            if min_version is not None and LooseVersion(version) < min_version:
                raise PkgConfigError(name)
            ext.extra_compile_args.extend(get_output("--cflags"))
            ext.extra_link_args.extend(get_output("--libs"))
        except subprocess.CalledProcessError:
            return self._check_fallback_header(
                ext, name, fallback_header, fallback_name)

    def _check_fallback_header(self, ext, name, header, fallback_name):
        if header is None:
            raise PkgConfigError(name)
        if header not in self._header_cache:
            # Workaround lack of TemporaryDirectory and subprocess.DEVNULL on
            # Py2.7.
            tmpdir = None
            try:
                tmpdir = tempfile.mkdtemp()
                with open(os.path.join(tmpdir, "setup.py"), "w") as file:
                    file.write(
                        "from setuptools import setup, Extension\n"
                        "setup(ext_modules=[Extension('test', ['test.c'])])")
                with open(os.path.join(tmpdir, "test.c"), "w") as file:
                    file.write(
                        "#include <Python.h>\n"
                        "#include <{}>\n"
                        "PyMODINIT_FUNC\n"
                        "{}(void) {{}}"
                        .format(header,
                                "inittest" if sys.version_info < (3,)
                                else "PyInit_test"))
                with open(os.devnull, "w") as devnull:
                    self._header_cache[header] = subprocess.call(
                        [sys.executable, "setup.py", "build"], cwd=tmpdir,
                        stdout=devnull, stderr=devnull) == 0
            finally:
                if tmpdir is not None:
                    shutil.rmtree(tmpdir)
        if self._header_cache[header]:
            ext.libraries.append(fallback_name or name)
        else:
            raise PkgConfigError(name)


pkg_config = _PkgConfig()


class Matplotlib(Package):
    packages = setuptools.find_packages(
        "lib",
        include=["matplotlib", "matplotlib.*"],
        exclude=["matplotlib.tests", "matplotlib.sphinxext.tests"])
    py_modules = ["pylab"]
    package_data = {
        "matplotlib": [
            # Work around lack of rglob on Py2.
            os.path.relpath(os.path.join(dirpath, filename), "lib/matplotlib")
            for data_dir in ["mpl-data/fonts",
                             "mpl-data/images",
                             "mpl-data/stylelib",
                             "backends/web_backend"]
            for dirpath, _, filenames in os.walk(os.path.join("lib/matplotlib",
                                                              data_dir))
            for filename in filenames]
        + ["mpl-data/matplotlibrc"]
    }


# install_requires.

class Numpy(Package):
    install_requires = ["numpy>=1.7.1"]

    @staticmethod
    def add_flags(ext):

        @ext.include_dirs.append
        @delayed_str
        def _get_include():
            import numpy as np
            return np.get_include()

        # PY_ARRAY_UNIQUE_SYMBOL must be uniquely defined for each extension.
        array_api_name = "MPL_" + ext.name.replace(".", "_") + "_ARRAY_API"
        ext.define_macros.append(("PY_ARRAY_UNIQUE_SYMBOL", array_api_name))
        ext.define_macros.append(("NPY_NO_DEPRECATED_API",
                                  "NPY_1_7_API_VERSION"))
        # Allow NumPy"s printf format specifiers in C++.
        ext.define_macros.append(("__STDC_FORMAT_MACROS", 1))


class PurePythonRequires(Package):
    install_requires = [
        "cycler>=0.10",
        "python-dateutil>=2.0",
        "pyparsing>=2.0.1,!=2.0.4,!=2.1.2,!=2.1.6",
        "pytz",
        "six>=1.10"]
    extras_require = {
        ":python_version<'3'": ["backports.functools_lru_cache"],
        ":python_version<'3' and os_name=='posix'": ["subprocess32"]}


# Binary dependencies, not listed in the package list.

class FreeType(Package):
    @staticmethod
    def add_flags(ext):
        # Note: 9.11.3 is the pkg-config version corresponding to freetype
        # 2.3.0.  The former can be read from builds/unix/configure.raw in
        # the freetype2 source tree.
        # See also the setting of include paths above for Windows + conda.
        pkg_config.add_flags(
            ext,
            "freetype" if sys.platform == "win32" else "freetype2",
            min_version="9.11.3",
            alt_exec="freetype-config",
            fallback_header="ft2build.h")


class Gtk(Package):
    @classmethod
    def add_flags(cls, ext):
        try:
            pkg_config.add_flags(ext, "pygtk-2.0", min_version="2.2.0",
                                 fallback_header="pygtk/pygtk.h")
        except PkgConfigError:
            if sys.platform == "win32":
                ext.library_dirs.extend(["C:/GTK/bin", "C:/GTK/lib"])
                ext.include_dirs.extend([
                    "win32_static/include/pygtk-2.0",
                    "C:/GTK/include",
                    "C:/GTK/include/gobject",
                    "C:/GTK/include/gext",
                    "C:/GTK/include/glib",
                    "C:/GTK/include/pango",
                    "C:/GTK/include/atk",
                    "C:/GTK/include/X11",
                    "C:/GTK/include/cairo",
                    "C:/GTK/include/gdk",
                    "C:/GTK/include/gdk-pixbuf",
                    "C:/GTK/include/gtk"
                ])


class LibAgg_headers_only(Package):
    @classmethod
    def add_flags(cls, ext):
        # Don't bother supporting building from a non-vendored version for now.
        ext.include_dirs.append("extern/agg24-svn/include")


class LibAgg(Package):
    @classmethod
    def add_flags(cls, ext):
        # Don't bother supporting building from a non-vendored version for now.
        ext.include_dirs.append("extern/agg24-svn/include")
        ext.sources.extend([
            "extern/agg24-svn/src/agg_bezier_arc.cpp",
            "extern/agg24-svn/src/agg_curves.cpp",
            "extern/agg24-svn/src/agg_image_filters.cpp",
            "extern/agg24-svn/src/agg_trans_affine.cpp",
            "extern/agg24-svn/src/agg_vcgen_contour.cpp",
            "extern/agg24-svn/src/agg_vcgen_dash.cpp",
            "extern/agg24-svn/src/agg_vcgen_stroke.cpp",
            "extern/agg24-svn/src/agg_vpgen_segmentator.cpp"])


class LibPng(Package):
    @staticmethod
    def add_flags(ext):
        if (sys.platform == "win32"
                and get_enum_config("windows", "libpng",
                                    ["static", "dynamic"])
                    == "static"):
            ext.libraries.append("libpng_static")
            ext.libraries.append("zlibstatic")
        else:
            pkg_config.add_flags(ext, "libpng", min_version="1.2",
                                 alt_exec="libpng-config",
                                 fallback_header="png.h", fallback_name="png")


class Qhull(Package):
    @staticmethod
    def add_flags(ext):
        try:
            pkg_config.add_flags(ext, "libqhull", min_version="2015.2",
                                 fallback_header="libqhull/qhull_a.h")
        except PkgConfigError:
            ext.include_dirs.append("extern")
            ext.sources.extend(sorted(glob.glob("extern/libqhull/*.c")))


# Extension modules.

class Contour(Package):
    ext_modules = [
        with_dependencies(Extension(
            "matplotlib._contour",
            ["src/_contour.cpp",
             "src/_contour_wrapper.cpp"]),
            [Numpy]),
        # DEPRECATED.
        with_dependencies(Extension(
            "matplotlib._cntr",
            ["src/cntr.c"]),
            [Numpy])]


class FT2Font(Package):
    ext_modules = [with_dependencies(Extension(
        "matplotlib.ft2font",
        ["src/ft2font.cpp",
         "src/ft2font_wrapper.cpp",
         "src/mplutils.cpp"]),
        [FreeType, Numpy])]


class Image(Package):
    ext_modules = [with_dependencies(Extension(
        "matplotlib._image",
        ["src/_image.cpp",
         "src/_image_wrapper.cpp",
         "src/mplutils.cpp",
         "src/py_converters.cpp"]),
        [LibAgg, Numpy])]


class Path(Package):
    ext_modules = [with_dependencies(Extension(
        "matplotlib._path",
        ["src/_path_wrapper.cpp",
         "src/py_converters.cpp"]),
        [LibAgg, Numpy])]


class Png(Package):
    ext_modules = [with_dependencies(Extension(
        "matplotlib._png",
        ["src/_png.cpp",
         "src/mplutils.cpp"]),
        [LibPng, Numpy])]


class QhullWrap(Package):
    ext_modules = [with_dependencies(Extension(
        "matplotlib._qhull",
        ["src/qhull_wrap.c"],
        define_macros=[("MPL_DEVNULL", os.devnull)]),
        [Numpy, Qhull])]


class TTConv(Package):
    ext_modules = [with_dependencies(Extension(
        "matplotlib.ttconv",
        ["src/_ttconv.cpp",
         "extern/ttconv/pprdrv_tt.cpp",
         "extern/ttconv/pprdrv_tt2.cpp",
         "extern/ttconv/ttutil.cpp"],
        include_dirs=["extern"]),
        [Numpy])]


class Tri(Package):
    ext_modules = [with_dependencies(Extension(
        "matplotlib._tri",
        ["lib/matplotlib/tri/_tri.cpp",
         "lib/matplotlib/tri/_tri_wrapper.cpp",
         "src/mplutils.cpp"],
        include_dirs=["extern"]),
        [Numpy])]


# Optional packages.

class SampleData(Package):
    built = get_config("packages", "sample_data", True)
    package_data = {"matplotlib": ["mpl-data/sample_data/*"]}


class Toolkits(Package):
    built = get_config("packages", "toolkits", True)
    packages = setuptools.find_packages(
        "lib", include=["mpl_toolkits"], exclude=["mpl_toolkits.tests"])
    namespace_packages = ["mpl_toolkits"]


class Tests(Package):
    # FIXME extras_require (pytest, unittest.mock, etc.)
    built = get_config("packages", "tests", False)
    packages = ["matplotlib.tests", "matplotlib.sphinxext.tests"]
    package_data = {
        "matplotlib": [
            "tests/baseline_images/*/*",
            "tests/cmr10.pfb",
            "tests/mpltest.ttf",
            "tests/test_rcparams.rc",
            "tests/test_utf32_be_rcparams.rc",
            "sphinxext/tests/tinypages/*",
        ]
    }


class ToolkitsTests(Package):
    built = get_config("packages", "toolkits_tests",
                       Toolkits.built and Tests.built)
    if not (Toolkits.packages and Tests.packages):
        raise ValueError("'toolkits_tests' requires 'toolkits' and 'tests'")
    packages = ["mpl_toolkits.tests"]
    namespace_packages = ["mpl_toolkits"]
    package_data = {"mpl_toolkits": ["tests/baseline_images/*"]}


class Dlls(Package):
    # FIXME Needs to be actually implemented...
    built = False
    package_data = {"": ["*.dll"]}


# Backends, in topological order.

class BackendAgg(Package):
    provides_backend = "agg"
    ext_modules = [with_dependencies(Extension(
        "matplotlib.backends._backend_agg",
        ["src/_backend_agg.cpp",
         "src/_backend_agg_wrapper.cpp",
         "src/mplutils.cpp",
         "src/py_converters.cpp"]),
        [FreeType, LibAgg, Numpy])]


class BackendCairo(Package):
    provides_backend = "cairo"
    built = (_backports.has_module("cairocffi")
             or _backports.has_module("cairo"))


class BackendGtk(Package):
    # DEPRECATED.
    # NOTE: We technically require pygtk>=2.2, but that version was released in
    # 2004 whereas Py2.7 was released in 2010.
    built = _backports.has_module("gtk")
    provides_backend = "gtk"
    ext_modules = [with_dependencies(Extension(
        "matplotlib.backends._backend_gdk",
        ["src/_backend_gdk.c"]),
        [Gtk, Numpy])]
    package_data = {"matplotlib": ["mpl-data/*.glade"]}


class BackendWxAgg(Package):
    # NOTE: We technically require wx>=2.8, but that version was released in
    # 2006 whereas Py2.7 was released in 2010.
    built = _backports.has_module("wx")
    provides_backend = "wxagg"


class BackendTkAgg(Package):
    built = (_backports.has_module("tkinter")
             or _backports.has_module("Tkinter"))  # Py2.
    provides_backend = "tkagg"
    ext_modules = [with_dependencies(Extension(
        "matplotlib.backends._tkagg",
        ["src/_tkagg.cpp",
         "src/py_converters.cpp"],
        # PSAPI library needed for finding Tcl/Tk at run time.
        libraries=["psapi"] if sys.platform == "win32" else []),
        [LibAgg_headers_only, Numpy])]
    if sys.platform == "win32" and get_config("packages", "windowing", True):
        ext_modules.append(Extension(
            "matplotlib._windowing",
            ["src/_windowing.cpp"],
            include_dirs=["C:/include"],
            libraries=["user32"],
            library_dirs=["C:/lib"],
            extra_link_args=["-mwindows"]))


class BackendGtkAgg(Package):
    built = BackendGtk.built
    provides_backend = "gtk"
    extensions = [with_dependencies(Extension(
        "matplotlib.backends._gtkagg",
        ["src/_gtkagg.cpp",
         "src/mplutils.cpp",
         "src/py_converters.cpp"]),
        [Gtk, LibAgg, Numpy])]
    package_data = {"matplotlib": ["mpl-data/*.glade"]}


class BackendGtk3Agg(Package):
    with open(os.devnull, "w") as _devnull:  # Py2.7 workaround.
        built = subprocess.call(
            [sys.executable, "-c",
             "import gi; gi.require_version('Gtk', '3.0')"],
            stderr=_devnull) == 0
    provides_backend = "gtk3agg"
    package_data = {"matplotlib": ["mpl-data/*.glade"]}


class BackendQt4Agg(Package):
    built = _backports.has_module("PyQt4") or _backports.has_module("PySide")
    provides_backend = "qt4agg"


class BackendQt5Agg(Package):
    built = _backports.has_module("PyQt5")
    provides_backend = "qt5agg"


class BackendMacOSX(Package):
    built = sys.platform == "darwin"
    provides_backend = "macosx"
    ext_modules = [Extension(
        "matplotlib.backends._macosx",
        ["src/_macosx.m"],
        extra_link_args=["-framework", "Cocoa"])]


class BackendGtk3Cairo(Package):
    built = BackendGtk3Agg.built and BackendCairo.built
    provides_backend = "gtk3cairo"
