Modified APIs
`````````````
The following APIs have been modified:
- ``Axes.mouseover_set`` is now a frozenset, and deprecated.  Directly
  manipulate the artist's ``.mouseover`` attribute to change their mouseover
  status.

Removal of deprecated APIs
``````````````````````````
The following deprecated API elements have been removed:

- ``matplotlib.checkdep_tex``, ``matplotlib.checkdep_xmllint``,
- ``backend_bases.IdleEvent``,
- ``cbook.converter``, ``cbook.tostr``, ``cbook.todatetime``, ``cbook.todate``,
  ``cbook.tofloat``, ``cbook.toint``, ``cbook.unique``,
  ``cbook.is_string_like``, ``cbook.is_sequence_of_strings``,
  ``cbook.is_scalar``, ``cbook.soundex``, ``cbook.dict_delall``,
  ``cbook.get_split_ind``, ``cbook.wrap``, ``cbook.get_recursive_filelist``,
  ``cbook.pieces``, ``cbook.exception_to_str``, ``cbook.allequal``,
  ``cbook.alltrue``, ``cbook.onetrue``, ``cbook.allpairs``, ``cbook.finddir``,
  ``cbook.reverse_dict``, ``cbook.restrict_dict``, ``cbook.issubclass_safe``,
  ``cbook.recursive_remove``, ``cbook.unmasked_index_ranges``,
  ``cbook.Null``, ``cbook.RingBuffer``, ``cbook.Sorter``, ``cbook.Xlator``,
- ``font_manager.weight_as_number``, ``font_manager.ttfdict_to_fnames``,
- ``pyplot.colors``, ``pyplot.spectral``,
- ``rcsetup.validate_negative_linestyle``,
  ``rcsetup.validate_negative_linestyle_legacy``,
- ``testing.compare.verifiers``, ``testing.compare.verify``,
- ``testing.decorators.knownfailureif``,
  ``testing.decorators.ImageComparisonTest.remove_text``,
- ``tests.assert_str_equal``, ``tests.test_tinypages.file_same``,
- ``texmanager.dvipng_hack_alpha``,
- ``_AxesBase.axesPatch``, ``_AxesBase.set_color_cycle``,
  ``_AxesBase.get_cursor_props``, ``_AxesBase.set_cursor_props``,
- ``_ImageBase.iterpnames``,
- ``FigureCanvasBase.start_event_loop_default``;
- ``FigureCanvasBase.stop_event_loop_default``;
- ``Figure.figurePatch``,
- ``FigureCanvasBase.dynamic_update``, ``FigureCanvasBase.idle_event``,
  ``FigureCanvasBase.get_linestyle``, ``FigureCanvasBase.set_linestyle``,
- ``FigureCanvasQTAgg.blitbox``,
- passing non-numbers to ``EngFormatter.format_eng``,
- passing ``frac`` to ``PolarAxes.set_theta_grids``,
- any mention of idle events,
