Deprecations
````````````
The following modules are deprecated:

- :mod:`matplotlib.compat.subprocess`. This was a python 2 workaround, but all
  the functionality can now be found in the python 3 standard library
  :mod:`subprocess`.
- :mod:`matplotlib.backends.wx_compat`. Python 3 is only compatible with
  wxPython 4, so support for wxPython 3 or earlier can be dropped.

The following classes, methods, functions, and attributes are deprecated:

- ``afm.parse_afm``,
- ``backend_pgf.get_texcommand``,
- ``backend_ps.get_bbox``,
- ``backend_qt5.error_msg_qt``, ``backend_qt5.exception_handler``,
- ``backend_wx.FigureCanvasWx.macros``,
- ``cbook.GetRealpathAndStat``, ``cbook.Locked``,
- ``cbook.is_numlike`` (use ``isinstance(..., numbers.Number)`` instead),
  ``cbook.listFiles``, ``cbook.unicode_safe``,
- ``container.Container.set_remove_method``,
- ``contour.ContourLabeler.cl``, ``.cl_xy``, and ``.cl_cvalues``,
- ``dates.DateFormatter.strftime_pre_1900``, ``dates.DateFormatter.strftime``,
- ``font_manager.TempCache``,
- ``mathtext.unichr_safe`` (use ``chr`` instead),
- ``table.Table.get_child_artists`` (use ``get_children`` instead),
- ``testing.compare.ImageComparisonTest``, ``testing.compare.compare_float``,
- ``testing.decorators.CleanupTest``,
  ``testing.decorators.skip_if_command_unavailable``,
- ``FigureCanvasQT.keyAutoRepeat`` (directly check
  ``event.guiEvent.isAutoRepeat()`` in the event handler to decide whether to
  handle autorepeated key presses).
- ``FigureCanvasWx.macros``,
- ``_ImageBase.iterpnames``, use the ``interpolation_names`` property instead.
  (this affects classes that inherit from ``_ImageBase`` including
  :class:`FigureImage`, :class:`BboxImage`, and :class:`AxesImage`),
- ``texmanager.dvipng_hack_alpha``,
- ``text.Annotation.arrow``,

The following rcParams are deprecated:
- ``pgf.debug`` (the pgf backend relies on logging),
