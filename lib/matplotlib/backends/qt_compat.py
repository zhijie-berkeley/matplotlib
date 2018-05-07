"""
Qt binding and backend selector.

The selection logic is as follows:
- if any of PyQt5, PySide2, PyQt4 or PySide have already been imported
  (checked in that order), use it;
- otherwise, if the QT_API environment variable (used by Enthought) is
  set, use it to determine which binding to use (but do not change the
  backend based on it; i.e. if the Qt4Agg backend is requested but QT_API
  is set to "pyqt5", then actually use Qt4 with the binding specified by
  ``rcParams["backend.qt4"]``;
- otherwise, use whatever the rcParams indicate.
"""

from distutils.version import LooseVersion
import os
import sys

from matplotlib import rcParams


QT_API_PYQT5 = "PyQt5"
QT_API_PYSIDE2 = "PySide2"
QT_API_PYQTv2 = "PyQt4v2"
QT_API_PYSIDE = "PySide"
QT_API_PYQT = "PyQt4"
QT_API_ENV = os.environ.get('QT_API')
# First, check if anything is already imported.
if "PyQt5" in sys.modules:
    QT_API = rcParams["backend.qt5"] = QT_API_PYQT5
elif "PySide2" in sys.modules:
    QT_API = rcParams["backend.qt5"] = QT_API_PYSIDE2
elif "PyQt4" in sys.modules:
    QT_API = rcParams["backend.qt4"] = QT_API_PYQTv2
elif "PySide" in sys.modules:
    QT_API = rcParams["backend.qt4"] = QT_API_PYSIDE
# Otherwise, check the QT_API environment variable (from Enthought).  This can
# only override the binding, not the backend (in other words, we check that the
# requested backend actually matches).
elif rcParams["backend"] == "Qt5Agg":
    if QT_API_ENV == "pyqt5":
        rcParams["backend.qt5"] = QT_API_PYQT5
    elif QT_API_ENV == "pyside2":
        rcParams["backend.qt5"] = QT_API_PYSIDE2
    QT_API = rcParams["backend.qt5"]
elif rcParams["backend"] == "Qt4Agg":
    if QT_API_ENV == "pyqt4":
        rcParams["backend.qt4"] = QT_API_PYQTv2
    elif QT_API_ENV == "pyside":
        rcParams["backend.qt4"] = QT_API_PYSIDE
    QT_API = rcParams["backend.qt5"]
# A non-Qt backend was selected but we still got there (possible, e.g., when
# fully manually embedding Matplotlib in a Qt app without using pyplot).
else:
    QT_API = None


def _setup_pyqt5():
    global QtCore, QtGui, QtWidgets, __version__, is_pyqt5, _getSaveFileName

    if QT_API == QT_API_PYQT5:
        from PyQt5 import QtCore, QtGui, QtWidgets
        __version__ = QtCore.PYQT_VERSION_STR
        QtCore.Signal = QtCore.pyqtSignal
        QtCore.Slot = QtCore.pyqtSlot
        QtCore.Property = QtCore.pyqtProperty
    elif QT_API == QT_API_PYSIDE2:
        from PySide2 import QtCore, QtGui, QtWidgets, __version__
    else:
        raise ValueError("Unexpected value for the 'backend.qt5' rcparam")
    _getSaveFileName = QtWidgets.QFileDialog.getSaveFileName

    def is_pyqt5():
        return True


def _setup_pyqt4():
    global QtCore, QtGui, QtWidgets, __version__, is_pyqt5, _getSaveFileName

    def _setup_pyqt4_internal(api):
        global QtCore, QtGui, QtWidgets, \
            __version__, is_pyqt5, _getSaveFileName
        # List of incompatible APIs:
        # http://pyqt.sourceforge.net/Docs/PyQt4/incompatible_apis.html
        _sip_apis = ["QDate", "QDateTime", "QString", "QTextStream", "QTime",
                     "QUrl", "QVariant"]
        import sip
        for _sip_api in _sip_apis:
            try:
                sip.setapi(_sip_api, api)
            except ValueError:
                pass
        from PyQt4 import QtCore, QtGui
        __version__ = QtCore.PYQT_VERSION_STR
        # PyQt 4.6 introduced getSaveFileNameAndFilter:
        # https://riverbankcomputing.com/news/pyqt-46
        if __version__ < LooseVersion(str("4.6")):
            raise ImportError("PyQt<4.6 is not supported")
        QtCore.Signal = QtCore.pyqtSignal
        QtCore.Slot = QtCore.pyqtSlot
        QtCore.Property = QtCore.pyqtProperty
        _getSaveFileName = QtGui.QFileDialog.getSaveFileNameAndFilter

    if QT_API == QT_API_PYQTv2:
        _setup_pyqt4_internal(api=2)
    elif QT_API == QT_API_PYSIDE:
        from PySide import QtCore, QtGui, __version__, __version_info__
        # PySide 1.0.3 fixed the following:
        # https://srinikom.github.io/pyside-bz-archive/809.html
        if __version_info__ < (1, 0, 3):
            raise ImportError("PySide<1.0.3 is not supported")
        _getSaveFileName = QtGui.QFileDialog.getSaveFileName
    elif QT_API == QT_API_PYQT:
        _setup_pyqt4_internal(api=1)
    else:
        raise ValueError("Unexpected value for the 'backend.qt4' rcparam")
    QtWidgets = QtGui

    def is_pyqt5():
        return False


if QT_API in [QT_API_PYQT5, QT_API_PYSIDE2]:
    _setup_pyqt5()
elif QT_API in [QT_API_PYQT, QT_API_PYQTv2, QT_API_PYSIDE]:
    _setup_pyqt4()
elif QT_API is None:
    for _setup, QT_API in [(_setup_pyqt5, QT_API_PYQT5),
                           (_setup_pyqt5, QT_API_PYSIDE2),
                           (_setup_pyqt4, QT_API_PYQTv2),
                           (_setup_pyqt4, QT_API_PYSIDE),
                           (_setup_pyqt4, QT_API_PYQT)]:
        try:
            _setup()
        except ImportError:
            continue
        break
    else:
        raise ImportError("Failed to import any qt binding")
else:
    raise RuntimeError  # We should not get there.


# These globals are only defined for backcompatibilty purposes.
ETS = dict(pyqt=(QT_API_PYQTv2, 4), pyside=(QT_API_PYSIDE, 4),
           pyqt5=(QT_API_PYQT5, 5), pyside2=(QT_API_PYSIDE2, 5))
QT_RC_MAJOR_VERSION = 5 if is_pyqt5() else 4
