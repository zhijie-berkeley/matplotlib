"""
setup.py for Matplotlib.

Build options can be modified using a configuration file.  Its filename, which
defaults to setup.cfg, can be overridden using the MPLSETUPCFG environment
variable.  See setup.cfg.template for more information.
"""

from __future__ import print_function, absolute_import

from distutils.version import LooseVersion
from string import Template
import sys

if sys.version_info < (2, 7):
    sys.exit("Python>=2.7 is required.")

try:
    # Required to support environment markers in extras_require.
    _setuptools_min_version = "18.0"
    import setuptools
except ImportError:
    sys.exit("setuptools>={} is required; "
             "install with 'pip install setuptools'."
             .format(_setuptools_min_version))
if LooseVersion(setuptools.__version__) < _setuptools_min_version:
    sys.exit("setuptools>={} is required (found setuptools {}); "
             "update with 'pip install -U setuptools'."
             .format(_setuptools_min_version, setuptools.__version__))

import versioneer

import _setupext
from _setupext import OPTIONS


mpl_packages = [
    _setupext.Matplotlib,
    # install_requires.
    _setupext.Numpy,
    _setupext.PurePythonRequires,
    # Extension modules.
    _setupext.Contour,
    _setupext.FT2Font,
    _setupext.Image,
    _setupext.Path,
    _setupext.Png,
    _setupext.QhullWrap,
    _setupext.TTConv,
    _setupext.Tri,
    # Optional packages.
    _setupext.SampleData,
    _setupext.Toolkits,
    _setupext.Tests,
    _setupext.ToolkitsTests,
    _setupext.Dlls,
    # Backends, from least to most preferred.
    _setupext.BackendCairo,
    _setupext.BackendAgg,
    _setupext.BackendGtk,
    _setupext.BackendWxAgg,
    _setupext.BackendTkAgg,
    _setupext.BackendGtkAgg,
    _setupext.BackendGtk3Cairo,
    _setupext.BackendGtk3Agg,
    _setupext.BackendQt4Agg,
    _setupext.BackendQt5Agg,
    _setupext.BackendMacOSX,
]


setup_kwargs = dict(
    name="matplotlib",
    version=versioneer.get_version(),
    description="Python plotting package",
    author="John D. Hunter, Michael Droettboom",
    author_email="matplotlib-users@python.org",
    url="http://matplotlib.org",
    download_url="http://matplotlib.org/users/installing.html",
    long_description="""
    Matplotlib strives to produce publication quality 2D graphics for
    interactive graphing, scientific publishing, user interface development and
    web application servers targeting multiple user interfaces and hardcopy
    output formats.  There is a "pylab" mode which emulates MATLAB graphics.
    """,
    license="BSD",
    platforms="any",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Python Software Foundation License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering :: Visualization",
    ],
    zip_safe=False,
    cmdclass=versioneer.get_cmdclass(),
    package_dir={"": "lib"},
    python_requires=">=2.7",
    install_requires=[],
    extras_require={},
    packages=[],
    namespace_packages=[],
    py_modules=[],
    ext_modules=[],
    package_data={},
)


def _process_packages():
    max_len = max(len(pkg.__name__) for pkg in mpl_packages)
    default_backend = "agg"
    for pkg in mpl_packages:
        _setupext.log("{:>{}}: {}".format(
            pkg.__name__, max_len,
            {True: "yes", False: "no"}[pkg.built]))
        pkg.register(setup_kwargs)
        if pkg.built and pkg.provides_backend:
            default_backend = pkg.provides_backend
    if OPTIONS["backend"] is not None:
        default_backend = options["backend"]
    with open("matplotlibrc.template") as file:
        template = file.read()
    template = Template(template)
    with open("lib/matplotlib/mpl-data/matplotlibrc", "w") as file:
        file.write(template.safe_substitute(TEMPLATE_BACKEND=default_backend))


_process_packages()
setuptools.setup(**setup_kwargs)
