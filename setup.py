"""
setup.py for Matplotlib.

Build options can be modified using a configuration file.  Its filename, which
defaults to setup.cfg, can be overridden using the MPLSETUPCFG environment
variable.  See setup.cfg.template for more information.
"""

from __future__ import print_function, absolute_import

from distutils.version import LooseVersion
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

if set(sys.argv[1:]) & {
        "bdist_wheel", "build", "build_ext", "build_py", "develop", "egg_info",
        "install", "sdist"}:
    # _setupext does a lot of work at import time, so delay the import until it
    # is necessary.
    import _setupext
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
    setup_kwargs = _setupext.process_packages(mpl_packages, setup_kwargs)

setuptools.setup(**setup_kwargs)
