"""
Classes for the ticks and x and y axis
"""

import datetime
import logging
import warnings

import numpy as np

from matplotlib import rcParams
import matplotlib.artist as artist
from matplotlib.artist import allow_rasterization
import matplotlib.cbook as cbook
from matplotlib.cbook import _string_to_bool
import matplotlib.font_manager as font_manager
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.scale as mscale
import matplotlib.text as mtext
import matplotlib.ticker as mticker
import matplotlib.transforms as mtransforms
import matplotlib.units as munits

_log = logging.getLogger(__name__)

GRIDLINE_INTERPOLATION_STEPS = 180

# This list is being used for compatibility with Axes.grid, which
# allows all Line2D kwargs.
_line_AI = artist.ArtistInspector(mlines.Line2D)
_line_param_names = _line_AI.get_setters()
_line_param_aliases = [list(d.keys())[0] for d in _line_AI.aliasd.values()]
_gridline_param_names = ['grid_' + name
                         for name in _line_param_names + _line_param_aliases]


class TickCollection(artist.Artist):

    def __init__(self, axis, *,
                 which="major",
                 grid_linestyle=None,
                 grid_linewidth=None,
                 grid_color=None,
                 grid_alpha=None,
                 pad=None,
                 labelsize=None,
                 labelcolor=None):

        super().__init__()
        self._axis = axis
        self._which = which

        self._grid_linestyle = (
            grid_linestyle if grid_linestyle is not None
            else rcParams["grid.linestyle"])
        self._grid_linewidth = (
            grid_linewidth if grid_linewidth is not None
            else rcParams["grid.linewidth"])
        self._grid_color = (
            grid_color if grid_color is not None
            else rcParams["grid.color"])
        self._grid_alpha = (
            grid_alpha if grid_alpha is not None
            else rcParams["grid.alpha"])
        self._pad = (
            pad if pad is not None
            else rcParams["{}.{}.size".format(self.__name__, which)])
        self._labelsize = (
            labelsize if labelsize is not None
            else rcParams["{}.labelsize".format(self.__name__)])
        self._labelcolor = (
            labelcolor if labelcolor is not None
            else rcParams["{}.color".format(self.__name__)])

        self._grid = mlines.Line2D([], [], **self._grid_kwargs)
        self._tick1 = mlines.Line2D([], [], c="k", ls="none")
        self._tick2 = mlines.Line2D([], [], c="k", ls="none")
        self._text1s = []
        self._text2s = []
        self._text1_visible = True
        self._text2_visible = True

    axes = property(lambda self: self._axis.axes)
    _grid_kwargs = property(lambda self: {
        "linestyle": self._grid_linestyle,
        "linewidth": self._grid_linewidth,
        "color": self._grid_color,
        "alpha": self._grid_alpha,
    })
    _text_kwargs = property(lambda self: {
        "fontproperties": font_manager.FontProperties(size=self._labelsize),
        "color": self._labelcolor,
    })

    def _apply_params(self, *,
                      gridOn=None,
                      tick1On=None,
                      tick2On=None,
                      label1On=None,
                      label2On=None):
        if gridOn is not None:
            self._grid.set_visible(gridOn)
        if tick1On is not None:
            self._tick1.set_visible(tick1On)
        if tick2On is not None:
            self._tick2.set_visible(tick2On)
        if label1On is not None:
            self._text1_visible = label1On
        if label2On is not None:
            self._text2_visible = label2On

    def get_labelsize(self):
        return (np.mean([text.get_size()
                         for text in [*self._text1s, *self._text2s]])
                if self._text1s or self._text2s else 0)

    def locate_and_format(self):
        raise NotImplementedError

    def draw(self, renderer):
        self._grid.draw(renderer)
        self._tick1.draw(renderer)
        self._tick2.draw(renderer)
        for text in [*self._text1s, *self._text2s]:
            text.draw(renderer)


class XTickCollection(TickCollection):
    __name__ = "xtick"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tick1.set_marker(mlines.TICKDOWN)
        self._tick2.set_marker(mlines.TICKUP)

    def locate_and_format(self):
        low, high = self.axes.viewLim.intervalx
        positions = [x for x in self.locator() if low <= x <= high]
        self._grid.set_data(np.repeat(positions, 3),
                            np.tile([0, 1, np.nan], len(positions)))
        self._grid.set_transform(self.axes.get_xaxis_transform("grid"))
        self._tick1.set_data(positions, np.zeros_like(positions))
        self._tick1.set_transform(self.axes.get_xaxis_transform("tick1"))
        self._tick2.set_data(positions, np.ones_like(positions))
        self._tick2.set_transform(self.axes.get_xaxis_transform("tick2"))
        self.formatter.set_locs(positions)
        labels = [self.formatter(pos, i) for i, pos in enumerate(positions)]
        transform, va, ha = self.axes.get_xaxis_text1_transform(
            self._axis.labelpad + self._pad)
        self._text1s = [mtext.Text(pos, 0, label, transform=transform,
                                   va=va, ha=ha, visible=self._text1_visible,
                                   **self._text_kwargs)
                        for pos, label in zip(positions, labels)]
        for text in self._text1s:
            text.set_figure(self.axes.figure)
        transform, va, ha = self.axes.get_xaxis_text2_transform(
            self._axis.labelpad + self._pad)
        self._text2s = [mtext.Text(pos, 1, label, transform=transform,
                                   va=va, ha=ha, visible=self._text2_visible,
                                   **self._text_kwargs)
                        for pos, label in zip(positions, labels)]
        for text in self._text2s:
            text.set_figure(self.axes.figure)


class YTickCollection(TickCollection):
    __name__ = "ytick"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tick1.set_marker(mlines.TICKLEFT)
        self._tick2.set_marker(mlines.TICKRIGHT)

    def locate_and_format(self):
        low, high = self.axes.viewLim.intervaly
        positions = [y for y in self.locator() if low <= y <= high]
        self._grid.set_data(np.tile([0, 1, np.nan], len(positions)),
                            np.repeat(positions, 3))
        self._grid.set_transform(self.axes.get_yaxis_transform("grid"))
        self._tick1.set_data(np.zeros_like(positions), positions)
        self._tick1.set_transform(self.axes.get_yaxis_transform("tick1"))
        self._tick2.set_data(np.ones_like(positions), positions)
        self._tick2.set_transform(self.axes.get_yaxis_transform("tick2"))
        self.formatter.set_locs(positions)
        labels = [self.formatter(pos, i) for i, pos in enumerate(positions)]
        transform, va, ha = self.axes.get_yaxis_text1_transform(
            self._axis.labelpad + self._pad)
        self._text1s = [mtext.Text(0, pos, label, transform=transform,
                                   va=va, ha=ha, visible=self._text1_visible,
                                   **self._text_kwargs)
                        for pos, label in zip(positions, labels)]
        for text in self._text1s:
            text.set_figure(self.axes.figure)
        transform, va, ha = self.axes.get_yaxis_text2_transform(
            self._axis.labelpad + self._pad)
        self._text2s = [mtext.Text(1, pos, label, transform=transform,
                                   va=va, ha=ha, visible=self._text2_visible,
                                   **self._text_kwargs)
                        for pos, label in zip(positions, labels)]
        for text in self._text2s:
            text.set_figure(self.axes.figure)


class Axis(artist.Artist):
    """
    Public attributes

    * :attr:`axes.transData` - transform data coords to display coords
    * :attr:`axes.transAxes` - transform axis coords to display coords
    * :attr:`labelpad` - number of points between the axis and its label
    """
    OFFSETTEXTPAD = 3

    def __str__(self):
        return self.__class__.__name__ \
            + "(%f,%f)" % tuple(self.axes.transAxes.transform_point((0, 0)))

    def __init__(self, axes, pickradius=15):
        """
        Init the axis with the parent Axes instance
        """
        artist.Artist.__init__(self)
        self.set_figure(axes.figure)

        self.isDefault_label = True

        self.axes = axes

        self.major = type(self)._tick_collection_class(self, which="major")
        self.minor = type(self)._tick_collection_class(self, which="minor")

        self.callbacks = cbook.CallbackRegistry()

        self._autolabelpos = True
        self._smart_bounds = False

        self.label = self._get_label()
        self.labelpad = rcParams['axes.labelpad']
        self.offsetText = self._get_offset_text()

        self.pickradius = pickradius

        # Initialize here for testing; later add API
        self._major_tick_kw = dict()
        self._minor_tick_kw = dict()

        self.cla()
        self._set_scale('linear')

    def set_label_coords(self, x, y, transform=None):
        """
        Set the coordinates of the label.  By default, the x
        coordinate of the y label is determined by the tick label
        bounding boxes, but this can lead to poor alignment of
        multiple ylabels if there are multiple axes.  Ditto for the y
        coordinate of the x label.

        You can also specify the coordinate system of the label with
        the transform.  If None, the default coordinate system will be
        the axes coordinate system (0,0) is (left,bottom), (0.5, 0.5)
        is middle, etc

        """

        self._autolabelpos = False
        if transform is None:
            transform = self.axes.transAxes

        self.label.set_transform(transform)
        self.label.set_position((x, y))
        self.stale = True

    def get_transform(self):
        return self._scale.get_transform()

    def get_scale(self):
        return self._scale.name

    def _set_scale(self, value, **kwargs):
        self._scale = mscale.scale_factory(value, self, **kwargs)
        self._scale.set_default_locators_and_formatters(self)

        self.isDefault_majloc = True
        self.isDefault_minloc = True
        self.isDefault_majfmt = True
        self.isDefault_minfmt = True

    def limit_range_for_scale(self, vmin, vmax):
        return self._scale.limit_range_for_scale(vmin, vmax, self.get_minpos())

    @property
    @cbook.deprecated("2.2.0")
    def unit_data(self):
        return self.units

    @unit_data.setter
    @cbook.deprecated("2.2.0")
    def unit_data(self, unit_data):
        self.set_units(unit_data)

    def get_children(self):
        children = [self.label, self.offsetText]
        majorticks = self.get_major_ticks()
        minorticks = self.get_minor_ticks()

        children.extend(majorticks)
        children.extend(minorticks)
        return children

    def cla(self):
        'clear the current axis'

        self.label.set_text('')  # self.set_label_text would change isDefault_

        self._set_scale('linear')

        # Clear the callback registry for this axis, or it may "leak"
        self.callbacks = cbook.CallbackRegistry()

        # whether the grids are on
        self._gridOnMajor = (rcParams['axes.grid'] and
                             rcParams['axes.grid.which'] in ('both', 'major'))
        self._gridOnMinor = (rcParams['axes.grid'] and
                             rcParams['axes.grid.which'] in ('both', 'minor'))

        self.reset_ticks()

        self.converter = None
        self.units = None
        self.set_units(None)
        self.stale = True

    def reset_ticks(self):
        """
        Re-initialize the major and minor Tick lists.

        Each list starts with a single fresh Tick.
        """
        # Restore the lazy tick lists.
        try:
            del self.majorTicks
        except AttributeError:
            pass
        try:
            del self.minorTicks
        except AttributeError:
            pass
        try:
            self.set_clip_path(self.axes.patch)
        except AttributeError:
            pass

    def set_tick_params(self, which='major', reset=False, **kw):
        """
        Set appearance parameters for ticks, ticklabels, and gridlines.

        For documentation of keyword arguments, see
        :meth:`matplotlib.axes.Axes.tick_params`.
        """
        dicts = []
        if which == 'major' or which == 'both':
            dicts.append(self._major_tick_kw)
        if which == 'minor' or which == 'both':
            dicts.append(self._minor_tick_kw)
        kwtrans = self._translate_tick_kw(kw, to_init_kw=True)
        for d in dicts:
            if reset:
                d.clear()
            d.update(kwtrans)

        if reset:
            self.reset_ticks()
        else:
            if which == 'major' or which == 'both':
                self.major._apply_params(**self._major_tick_kw)
            if which == 'minor' or which == 'both':
                self.major._apply_params(**self._major_tick_kw)
            if 'labelcolor' in kwtrans:
                self.offsetText.set_color(kwtrans['labelcolor'])
        self.stale = True

    @staticmethod
    def _translate_tick_kw(kw, to_init_kw=True):
        # The following lists may be moved to a more
        # accessible location.
        kwkeys0 = ['size', 'width', 'color', 'tickdir', 'pad',
                   'labelsize', 'labelcolor', 'zorder', 'gridOn',
                   'tick1On', 'tick2On', 'label1On', 'label2On']
        kwkeys1 = ['length', 'direction', 'left', 'bottom', 'right', 'top',
                   'labelleft', 'labelbottom', 'labelright', 'labeltop',
                   'labelrotation']
        kwkeys2 = _gridline_param_names
        kwkeys = kwkeys0 + kwkeys1 + kwkeys2
        kwtrans = dict()
        if to_init_kw:
            if 'length' in kw:
                kwtrans['size'] = kw.pop('length')
            if 'direction' in kw:
                kwtrans['tickdir'] = kw.pop('direction')
            if 'rotation' in kw:
                kwtrans['labelrotation'] = kw.pop('rotation')
            if 'left' in kw:
                kwtrans['tick1On'] = _string_to_bool(kw.pop('left'))
            if 'bottom' in kw:
                kwtrans['tick1On'] = _string_to_bool(kw.pop('bottom'))
            if 'right' in kw:
                kwtrans['tick2On'] = _string_to_bool(kw.pop('right'))
            if 'top' in kw:
                kwtrans['tick2On'] = _string_to_bool(kw.pop('top'))

            if 'labelleft' in kw:
                kwtrans['label1On'] = _string_to_bool(kw.pop('labelleft'))
            if 'labelbottom' in kw:
                kwtrans['label1On'] = _string_to_bool(kw.pop('labelbottom'))
            if 'labelright' in kw:
                kwtrans['label2On'] = _string_to_bool(kw.pop('labelright'))
            if 'labeltop' in kw:
                kwtrans['label2On'] = _string_to_bool(kw.pop('labeltop'))
            if 'colors' in kw:
                c = kw.pop('colors')
                kwtrans['color'] = c
                kwtrans['labelcolor'] = c
            # Maybe move the checking up to the caller of this method.
            for key in kw:
                if key not in kwkeys:
                    raise ValueError(
                        "keyword %s is not recognized; valid keywords are %s"
                        % (key, kwkeys))
            kwtrans.update(kw)
        else:
            raise NotImplementedError("Inverse translation is deferred")
        return kwtrans

    def get_view_interval(self):
        'return the Interval instance for this axis view limits'
        raise NotImplementedError('Derived must override')

    def set_view_interval(self, vmin, vmax, ignore=False):
        raise NotImplementedError('Derived must override')

    def get_data_interval(self):
        'return the Interval instance for this axis data limits'
        raise NotImplementedError('Derived must override')

    def set_data_interval(self):
        '''set the axis data limits'''
        raise NotImplementedError('Derived must override')

    def set_default_intervals(self):
        '''set the default limits for the axis data and view interval if they
        are not mutated'''

        # this is mainly in support of custom object plotting.  For
        # example, if someone passes in a datetime object, we do not
        # know automagically how to set the default min/max of the
        # data and view limits.  The unit conversion AxisInfo
        # interface provides a hook for custom types to register
        # default limits through the AxisInfo.default_limits
        # attribute, and the derived code below will check for that
        # and use it if is available (else just use 0..1)
        pass

    def _set_artist_props(self, a):
        if a is None:
            return
        a.set_figure(self.figure)

    def get_ticklabel_extents(self, renderer):
        """
        Get the extents of the tick labels on either side
        of the axes.
        """

        ticks_to_draw = self._update_ticks(renderer)
        ticklabelBoxes, ticklabelBoxes2 = self._get_tick_bboxes(ticks_to_draw,
                                                                renderer)

        if len(ticklabelBoxes):
            bbox = mtransforms.Bbox.union(ticklabelBoxes)
        else:
            bbox = mtransforms.Bbox.from_extents(0, 0, 0, 0)
        if len(ticklabelBoxes2):
            bbox2 = mtransforms.Bbox.union(ticklabelBoxes2)
        else:
            bbox2 = mtransforms.Bbox.from_extents(0, 0, 0, 0)
        return bbox, bbox2

    def set_smart_bounds(self, value):
        """set the axis to have smart bounds"""
        self._smart_bounds = value
        self.stale = True

    def get_smart_bounds(self):
        """get whether the axis has smart bounds"""
        return self._smart_bounds

    def _update_ticks(self, renderer):
        """
        Update ticks (position and labels) using the current data
        interval of the axes. Returns a list of ticks that will be
        drawn.
        """
        self.major.locate_and_format()
        self.minor.locate_and_format()

    def get_tightbbox(self, renderer):
        """
        Return a bounding box that encloses the axis. It only accounts
        tick labels, axis label, and offsetText.
        """
        if not self.get_visible():
            return

        ticks_to_draw = self._update_ticks(renderer)

        self._update_label_position(renderer)

        # go back to just this axis's tick labels
        ticklabelBoxes, ticklabelBoxes2 = self._get_tick_bboxes(
                    ticks_to_draw, renderer)

        self._update_offset_text_position(ticklabelBoxes, ticklabelBoxes2)
        self.offsetText.set_text(self.major.formatter.get_offset())

        bb = []

        for a in [self.label, self.offsetText]:
            if a.get_visible():
                bb.append(a.get_window_extent(renderer))

        bb.extend(ticklabelBoxes)
        bb.extend(ticklabelBoxes2)

        bb = [b for b in bb if b.width != 0 or b.height != 0]
        if bb:
            _bbox = mtransforms.Bbox.union(bb)
            return _bbox
        else:
            return None

    def get_tick_padding(self):
        values = []
        if len(self.majorTicks):
            values.append(self.majorTicks[0].get_tick_padding())
        if len(self.minorTicks):
            values.append(self.minorTicks[0].get_tick_padding())
        return max(values, default=0)

    @allow_rasterization
    def draw(self, renderer, *args, **kwargs):
        'Draw the axis lines, grid lines, tick lines and labels'

        if not self.get_visible():
            return
        renderer.open_group(__name__)

        self._update_ticks(renderer)
        self.major.draw(renderer)
        self.minor.draw(renderer)
        self.label.draw(renderer)

        renderer.close_group(__name__)
        self.stale = False

    def _get_label(self):
        raise NotImplementedError('Derived must override')

    def _get_offset_text(self):
        raise NotImplementedError('Derived must override')

    def get_gridlines(self):
        'Return the grid lines as a list of Line2D instance'
        ticks = self.get_major_ticks()
        return cbook.silent_list('Line2D gridline',
                                 [tick.gridline for tick in ticks])

    def get_label(self):
        'Return the axis label as a Text instance'
        return self.label

    def get_offset_text(self):
        'Return the axis offsetText as a Text instance'
        return self.offsetText

    def get_pickradius(self):
        'Return the depth of the axis used by the picker'
        return self.pickradius

    def get_majorticklabels(self):
        'Return a list of Text instances for the major ticklabels'
        ticks = self.get_major_ticks()
        labels1 = [tick.label1 for tick in ticks if tick.label1On]
        labels2 = [tick.label2 for tick in ticks if tick.label2On]
        return cbook.silent_list('Text major ticklabel', labels1 + labels2)

    def get_minorticklabels(self):
        'Return a list of Text instances for the minor ticklabels'
        ticks = self.get_minor_ticks()
        labels1 = [tick.label1 for tick in ticks if tick.label1On]
        labels2 = [tick.label2 for tick in ticks if tick.label2On]
        return cbook.silent_list('Text minor ticklabel', labels1 + labels2)

    def get_ticklabels(self, minor=False, which=None):
        """
        Get the x tick labels as a list of :class:`~matplotlib.text.Text`
        instances.

        Parameters
        ----------
        minor : bool
           If True return the minor ticklabels,
           else return the major ticklabels

        which : None, ('minor', 'major', 'both')
           Overrides `minor`.

           Selects which ticklabels to return

        Returns
        -------
        ret : list
           List of :class:`~matplotlib.text.Text` instances.
        """

        if which is not None:
            if which == 'minor':
                return self.get_minorticklabels()
            elif which == 'major':
                return self.get_majorticklabels()
            elif which == 'both':
                return self.get_majorticklabels() + self.get_minorticklabels()
            else:
                raise ValueError("`which` must be one of ('minor', 'major', "
                                 "'both') not " + str(which))
        if minor:
            return self.get_minorticklabels()
        return self.get_majorticklabels()

    def get_majorticklines(self):
        'Return the major tick lines as a list of Line2D instances'
        lines = []
        ticks = self.get_major_ticks()
        for tick in ticks:
            lines.append(tick.tick1line)
            lines.append(tick.tick2line)
        return cbook.silent_list('Line2D ticklines', lines)

    def get_minorticklines(self):
        'Return the minor tick lines as a list of Line2D instances'
        lines = []
        ticks = self.get_minor_ticks()
        for tick in ticks:
            lines.append(tick.tick1line)
            lines.append(tick.tick2line)
        return cbook.silent_list('Line2D ticklines', lines)

    def get_ticklines(self, minor=False):
        'Return the tick lines as a list of Line2D instances'
        if minor:
            return self.get_minorticklines()
        return self.get_majorticklines()

    def get_majorticklocs(self):
        "Get the major tick locations in data coordinates as a numpy array"
        return self.major.locator()

    def get_minorticklocs(self):
        "Get the minor tick locations in data coordinates as a numpy array"
        return self.minor.locator()

    def get_ticklocs(self, minor=False):
        "Get the tick locations in data coordinates as a numpy array"
        if minor:
            return self.minor.locator()
        return self.major.locator()

    def get_ticks_direction(self, minor=False):
        """
        Get the tick directions as a numpy array

        Parameters
        ----------
        minor : boolean
            True to return the minor tick directions,
            False to return the major tick directions,
            Default is False

        Returns
        -------
        numpy array of tick directions
        """
        if minor:
            return np.array(
                [tick._tickdir for tick in self.get_minor_ticks()])
        else:
            return np.array(
                [tick._tickdir for tick in self.get_major_ticks()])

    def _get_tick(self, major):
        'return the default tick instance'
        raise NotImplementedError('derived must override')

    def _copy_tick_props(self, src, dest):
        'Copy the props from src tick to dest tick'
        if src is None or dest is None:
            return
        dest.label1.update_from(src.label1)
        dest.label2.update_from(src.label2)

        dest.tick1line.update_from(src.tick1line)
        dest.tick2line.update_from(src.tick2line)
        dest.gridline.update_from(src.gridline)

        dest.tick1On = src.tick1On
        dest.tick2On = src.tick2On
        dest.label1On = src.label1On
        dest.label2On = src.label2On

    def get_label_text(self):
        'Get the text of the label'
        return self.label.get_text()

    def get_major_locator(self):
        'Get the locator of the major ticker'
        return self.major.locator

    def get_minor_locator(self):
        'Get the locator of the minor ticker'
        return self.minor.locator

    def get_major_formatter(self):
        'Get the formatter of the major ticker'
        return self.major.formatter

    def get_minor_formatter(self):
        'Get the formatter of the minor ticker'
        return self.minor.formatter

    def grid(self, b=None, which='major', **kwargs):
        """
        Set the axis grid on or off; b is a boolean. Use *which* =
        'major' | 'minor' | 'both' to set the grid for major or minor ticks.

        If *b* is *None* and len(kwargs)==0, toggle the grid state.  If
        *kwargs* are supplied, it is assumed you want the grid on and *b*
        will be set to True.

        *kwargs* are used to set the line properties of the grids, e.g.,

          xax.grid(color='r', linestyle='-', linewidth=2)
        """
        if len(kwargs):
            b = True
        which = which.lower()
        gridkw = {'grid_' + item[0]: item[1] for item in kwargs.items()}
        if which in ['minor', 'both']:
            if b is None:
                self._gridOnMinor = not self._gridOnMinor
            else:
                self._gridOnMinor = b
            self.set_tick_params(which='minor', gridOn=self._gridOnMinor,
                                 **gridkw)
        if which in ['major', 'both']:
            if b is None:
                self._gridOnMajor = not self._gridOnMajor
            else:
                self._gridOnMajor = b
            self.set_tick_params(which='major', gridOn=self._gridOnMajor,
                                 **gridkw)
        self.stale = True

    def update_units(self, data):
        """
        introspect *data* for units converter and update the
        axis.converter instance if necessary. Return *True*
        if *data* is registered for unit conversion.
        """

        converter = munits.registry.get_converter(data)
        if converter is None:
            return False

        neednew = self.converter != converter
        self.converter = converter
        default = self.converter.default_units(data, self)
        if default is not None and self.units is None:
            self.set_units(default)

        if neednew:
            self._update_axisinfo()
        self.stale = True
        return True

    def _update_axisinfo(self):
        """
        check the axis converter for the stored units to see if the
        axis info needs to be updated
        """
        if self.converter is None:
            return

        info = self.converter.axisinfo(self.units, self)

        if info is None:
            return
        if info.majloc is not None and \
           self.major.locator != info.majloc and self.isDefault_majloc:
            self.set_major_locator(info.majloc)
            self.isDefault_majloc = True
        if info.minloc is not None and \
           self.minor.locator != info.minloc and self.isDefault_minloc:
            self.set_minor_locator(info.minloc)
            self.isDefault_minloc = True
        if info.majfmt is not None and \
           self.major.formatter != info.majfmt and self.isDefault_majfmt:
            self.set_major_formatter(info.majfmt)
            self.isDefault_majfmt = True
        if info.minfmt is not None and \
           self.minor.formatter != info.minfmt and self.isDefault_minfmt:
            self.set_minor_formatter(info.minfmt)
            self.isDefault_minfmt = True
        if info.label is not None and self.isDefault_label:
            self.set_label_text(info.label)
            self.isDefault_label = True

        self.set_default_intervals()

    def have_units(self):
        return self.converter is not None or self.units is not None

    def convert_units(self, x):
        # If x is already a number, doesn't need converting
        if munits.ConversionInterface.is_numlike(x):
            return x

        if self.converter is None:
            self.converter = munits.registry.get_converter(x)

        if self.converter is None:
            return x

        ret = self.converter.convert(x, self.units, self)
        return ret

    def set_units(self, u):
        """
        set the units for axis

        ACCEPTS: a units tag
        """
        pchanged = False
        if u is None:
            self.units = None
            pchanged = True
        else:
            if u != self.units:
                self.units = u
                pchanged = True
        if pchanged:
            self._update_axisinfo()
            self.callbacks.process('units')
            self.callbacks.process('units finalize')
        self.stale = True

    def get_units(self):
        'return the units for axis'
        return self.units

    def set_label_text(self, label, fontdict=None, **kwargs):
        """  Sets the text value of the axis label

        ACCEPTS: A string value for the label
        """
        self.isDefault_label = False
        self.label.set_text(label)
        if fontdict is not None:
            self.label.update(fontdict)
        self.label.update(kwargs)
        self.stale = True
        return self.label

    def set_major_formatter(self, formatter):
        """
        Set the formatter of the major ticker

        ACCEPTS: A :class:`~matplotlib.ticker.Formatter` instance
        """
        if not isinstance(formatter, mticker.Formatter):
            raise TypeError("formatter argument should be instance of "
                    "matplotlib.ticker.Formatter")
        self.isDefault_majfmt = False
        self.major.formatter = formatter
        formatter.set_axis(self)
        self.stale = True

    def set_minor_formatter(self, formatter):
        """
        Set the formatter of the minor ticker

        ACCEPTS: A :class:`~matplotlib.ticker.Formatter` instance
        """
        if not isinstance(formatter, mticker.Formatter):
            raise TypeError("formatter argument should be instance of "
                    "matplotlib.ticker.Formatter")
        self.isDefault_minfmt = False
        self.minor.formatter = formatter
        formatter.set_axis(self)
        self.stale = True

    def set_major_locator(self, locator):
        """
        Set the locator of the major ticker

        ACCEPTS: a :class:`~matplotlib.ticker.Locator` instance
        """
        if not isinstance(locator, mticker.Locator):
            raise TypeError("formatter argument should be instance of "
                    "matplotlib.ticker.Locator")
        self.isDefault_majloc = False
        self.major.locator = locator
        locator.set_axis(self)
        self.stale = True

    def set_minor_locator(self, locator):
        """
        Set the locator of the minor ticker

        ACCEPTS: a :class:`~matplotlib.ticker.Locator` instance
        """
        if not isinstance(locator, mticker.Locator):
            raise TypeError("formatter argument should be instance of "
                    "matplotlib.ticker.Locator")
        self.isDefault_minloc = False
        self.minor.locator = locator
        locator.set_axis(self)
        self.stale = True

    def set_pickradius(self, pickradius):
        """
        Set the depth of the axis used by the picker

        ACCEPTS: a distance in points
        """
        self.pickradius = pickradius

    def set_ticklabels(self, ticklabels, *args, **kwargs):
        """
        Set the text values of the tick labels. Return a list of Text
        instances.  Use *kwarg* *minor=True* to select minor ticks.
        All other kwargs are used to update the text object properties.
        As for get_ticklabels, label1 (left or bottom) is
        affected for a given tick only if its label1On attribute
        is True, and similarly for label2.  The list of returned
        label text objects consists of all such label1 objects followed
        by all such label2 objects.

        The input *ticklabels* is assumed to match the set of
        tick locations, regardless of the state of label1On and
        label2On.

        ACCEPTS: sequence of strings or Text objects
        """
        get_labels = []
        for t in ticklabels:
            # try calling get_text() to check whether it is Text object
            # if it is Text, get label content
            try:
                get_labels.append(t.get_text())
            # otherwise add the label to the list directly
            except AttributeError:
                get_labels.append(t)
        # replace the ticklabels list with the processed one
        ticklabels = get_labels

        minor = kwargs.pop('minor', False)
        if minor:
            self.set_minor_formatter(mticker.FixedFormatter(ticklabels))
            ticks = self.get_minor_ticks()
        else:
            self.set_major_formatter(mticker.FixedFormatter(ticklabels))
            ticks = self.get_major_ticks()
        ret = []
        for tick_label, tick in zip(ticklabels, ticks):
            # deal with label1
            tick.label1.set_text(tick_label)
            tick.label1.update(kwargs)
            # deal with label2
            tick.label2.set_text(tick_label)
            tick.label2.update(kwargs)
            # only return visible tick labels
            if tick.label1On:
                ret.append(tick.label1)
            if tick.label2On:
                ret.append(tick.label2)

        self.stale = True
        return ret

    def set_ticks(self, ticks, minor=False):
        """
        Set the locations of the tick marks from sequence ticks

        ACCEPTS: sequence of floats
        """
        # XXX if the user changes units, the information will be lost here
        ticks = self.convert_units(ticks)
        if len(ticks) > 1:
            xleft, xright = self.get_view_interval()
            if xright > xleft:
                self.set_view_interval(min(ticks), max(ticks))
            else:
                self.set_view_interval(max(ticks), min(ticks))
        if minor:
            self.set_minor_locator(mticker.FixedLocator(ticks))
            return self.get_minor_ticks(len(ticks))
        else:
            self.set_major_locator(mticker.FixedLocator(ticks))
            return self.get_major_ticks(len(ticks))

    def pan(self, numsteps):
        'Pan *numsteps* (can be positive or negative)'
        self.major.locator.pan(numsteps)

    def zoom(self, direction):
        "Zoom in/out on axis; if *direction* is >0 zoom in, else zoom out"
        self.major.locator.zoom(direction)

    def axis_date(self, tz=None):
        """
        Sets up x-axis ticks and labels that treat the x data as dates.
        *tz* is a :class:`tzinfo` instance or a timezone string.
        This timezone is used to create date labels.
        """
        # By providing a sample datetime instance with the desired timezone,
        # the registered converter can be selected, and the "units" attribute,
        # which is the timezone, can be set.
        if isinstance(tz, str):
            import pytz
            tz = pytz.timezone(tz)
        self.update_units(datetime.datetime(2009, 1, 1, 0, 0, 0, 0, tz))

    def get_tick_space(self):
        """
        Return the estimated number of ticks that can fit on the axis.
        """
        # Must be overridden in the subclass
        raise NotImplementedError()

    def get_label_position(self):
        """
        Return the label position (top or bottom)
        """
        return self.label_position

    def set_label_position(self, position):
        """
        Set the label position (top or bottom)

        ACCEPTS: [ 'top' | 'bottom' ]
        """
        raise NotImplementedError()

    def get_minpos(self):
        raise NotImplementedError()


class XAxis(Axis):
    __name__ = 'xaxis'
    axis_name = 'x'
    _tick_collection_class = XTickCollection

    def contains(self, mouseevent):
        """Test whether the mouse event occurred in the x axis.
        """
        if callable(self._contains):
            return self._contains(self, mouseevent)

        x, y = mouseevent.x, mouseevent.y
        try:
            trans = self.axes.transAxes.inverted()
            xaxes, yaxes = trans.transform_point((x, y))
        except ValueError:
            return False, {}
        l, b = self.axes.transAxes.transform_point((0, 0))
        r, t = self.axes.transAxes.transform_point((1, 1))
        inaxis = 0 <= xaxes <= 1 and (
            b - self.pickradius < y < b or
            t < y < t + self.pickradius)
        return inaxis, {}

    def _get_label(self):
        # x in axes coords, y in display coords (to be updated at draw
        # time by _update_label_positions)
        label = mtext.Text(x=0.5, y=0,
                           fontproperties=font_manager.FontProperties(
                               size=rcParams['axes.labelsize'],
                               weight=rcParams['axes.labelweight']),
                           color=rcParams['axes.labelcolor'],
                           verticalalignment='top',
                           horizontalalignment='center')

        label.set_transform(mtransforms.blended_transform_factory(
            self.axes.transAxes, mtransforms.IdentityTransform()))

        self._set_artist_props(label)
        self.label_position = 'bottom'
        return label

    def _get_offset_text(self):
        # x in axes coords, y in display coords (to be updated at draw time)
        offsetText = mtext.Text(x=1, y=0,
                                fontproperties=font_manager.FontProperties(
                                    size=rcParams['xtick.labelsize']),
                                color=rcParams['xtick.color'],
                                verticalalignment='top',
                                horizontalalignment='right')
        offsetText.set_transform(mtransforms.blended_transform_factory(
            self.axes.transAxes, mtransforms.IdentityTransform())
        )
        self._set_artist_props(offsetText)
        self.offset_text_position = 'bottom'
        return offsetText

    def _get_pixel_distance_along_axis(self, where, perturb):
        """
        Returns the amount, in data coordinates, that a single pixel
        corresponds to in the locality given by "where", which is also given
        in data coordinates, and is an x coordinate. "perturb" is the amount
        to perturb the pixel.  Usually +0.5 or -0.5.

        Implementing this routine for an axis is optional; if present, it will
        ensure that no ticks are lost due to round-off at the extreme ends of
        an axis.
        """

        # Note that this routine does not work for a polar axis, because of
        # the 1e-10 below.  To do things correctly, we need to use rmax
        # instead of 1e-10 for a polar axis.  But since we do not have that
        # kind of information at this point, we just don't try to pad anything
        # for the theta axis of a polar plot.
        if self.axes.name == 'polar':
            return 0.0

        #
        # first figure out the pixel location of the "where" point.  We use
        # 1e-10 for the y point, so that we remain compatible with log axes.

        # transformation from data coords to display coords
        trans = self.axes.transData
        # transformation from display coords to data coords
        transinv = trans.inverted()
        pix = trans.transform_point((where, 1e-10))
        # perturb the pixel
        ptp = transinv.transform_point((pix[0] + perturb, pix[1]))
        dx = abs(ptp[0] - where)

        return dx

    def set_label_position(self, position):
        """
        Set the label position (top or bottom)

        ACCEPTS: [ 'top' | 'bottom' ]
        """
        if position == 'top':
            self.label.set_verticalalignment('baseline')
        elif position == 'bottom':
            self.label.set_verticalalignment('top')
        else:
            raise ValueError("Position accepts only 'top' or 'bottom'")
        self.label_position = position
        self.stale = True

    def _update_offset_text_position(self, bboxes, bboxes2):
        """
        Update the offset_text position based on the sequence of bounding
        boxes of all the ticklabels
        """
        x, y = self.offsetText.get_position()
        if not len(bboxes):
            bottom = self.axes.bbox.ymin
        else:
            bbox = mtransforms.Bbox.union(bboxes)
            bottom = bbox.y0
        self.offsetText.set_position(
            (x, bottom - self.OFFSETTEXTPAD * self.figure.dpi / 72)
        )

    def get_text_heights(self, renderer):
        """
        Returns the amount of space one should reserve for text
        above and below the axes.  Returns a tuple (above, below)
        """
        bbox, bbox2 = self.get_ticklabel_extents(renderer)
        # MGDTODO: Need a better way to get the pad
        padPixels = self.majorTicks[0].get_pad_pixels()

        above = 0.0
        if bbox2.height:
            above += bbox2.height + padPixels
        below = 0.0
        if bbox.height:
            below += bbox.height + padPixels

        if self.get_label_position() == 'top':
            above += self.label.get_window_extent(renderer).height + padPixels
        else:
            below += self.label.get_window_extent(renderer).height + padPixels
        return above, below

    def set_ticks_position(self, position):
        """
        Set the ticks position (top, bottom, both, default or none)
        both sets the ticks to appear on both positions, but does not
        change the tick labels.  'default' resets the tick positions to
        the default: ticks on both positions, labels at bottom.  'none'
        can be used if you don't want any ticks. 'none' and 'both'
        affect only the ticks, not the labels.

        ACCEPTS: [ 'top' | 'bottom' | 'both' | 'default' | 'none' ]
        """
        if position == 'top':
            self.set_tick_params(which='both', top=True, labeltop=True,
                                 bottom=False, labelbottom=False)
        elif position == 'bottom':
            self.set_tick_params(which='both', top=False, labeltop=False,
                                 bottom=True, labelbottom=True)
        elif position == 'both':
            self.set_tick_params(which='both', top=True,
                                 bottom=True)
        elif position == 'none':
            self.set_tick_params(which='both', top=False,
                                 bottom=False)
        elif position == 'default':
            self.set_tick_params(which='both', top=True, labeltop=False,
                                 bottom=True, labelbottom=True)
        else:
            raise ValueError("invalid position: %s" % position)
        self.stale = True

    def tick_top(self):
        """
        Move ticks and ticklabels (if present) to the top of the axes.
        """
        label = True
        if 'label1On' in self._major_tick_kw:
            label = (self._major_tick_kw['label1On']
                     or self._major_tick_kw['label2On'])
        self.set_ticks_position('top')
        # if labels were turned off before this was called
        # leave them off
        self.set_tick_params(which='both', labeltop=label)

    def tick_bottom(self):
        """
        Move ticks and ticklabels (if present) to the bottom of the axes.
        """
        label = True
        if 'label1On' in self._major_tick_kw:
            label = (self._major_tick_kw['label1On']
                     or self._major_tick_kw['label2On'])
        self.set_ticks_position('bottom')
        # if labels were turned off before this was called
        # leave them off
        self.set_tick_params(which='both', labelbottom=label)

    def get_ticks_position(self):
        """
        Return the ticks position (top, bottom, default or unknown)
        """
        majt = self.majorTicks[0]
        mT = self.minorTicks[0]

        majorTop = ((not majt.tick1On) and majt.tick2On and
                    (not majt.label1On) and majt.label2On)
        minorTop = ((not mT.tick1On) and mT.tick2On and
                    (not mT.label1On) and mT.label2On)
        if majorTop and minorTop:
            return 'top'

        MajorBottom = (majt.tick1On and (not majt.tick2On) and
                       majt.label1On and (not majt.label2On))
        MinorBottom = (mT.tick1On and (not mT.tick2On) and
                       mT.label1On and (not mT.label2On))
        if MajorBottom and MinorBottom:
            return 'bottom'

        majorDefault = (majt.tick1On and majt.tick2On and
                        majt.label1On and (not majt.label2On))
        minorDefault = (mT.tick1On and mT.tick2On and
                        mT.label1On and (not mT.label2On))
        if majorDefault and minorDefault:
            return 'default'

        return 'unknown'

    def get_view_interval(self):
        'return the Interval instance for this axis view limits'
        return self.axes.viewLim.intervalx

    def set_view_interval(self, vmin, vmax, ignore=False):
        """
        If *ignore* is *False*, the order of vmin, vmax
        does not matter; the original axis orientation will
        be preserved. In addition, the view limits can be
        expanded, but will not be reduced.  This method is
        for mpl internal use; for normal use, see
        :meth:`~matplotlib.axes.Axes.set_xlim`.

        """
        if ignore:
            self.axes.viewLim.intervalx = vmin, vmax
        else:
            Vmin, Vmax = self.get_view_interval()
            if Vmin < Vmax:
                self.axes.viewLim.intervalx = (min(vmin, vmax, Vmin),
                                               max(vmin, vmax, Vmax))
            else:
                self.axes.viewLim.intervalx = (max(vmin, vmax, Vmin),
                                               min(vmin, vmax, Vmax))

    def get_minpos(self):
        return self.axes.dataLim.minposx

    def get_data_interval(self):
        'return the Interval instance for this axis data limits'
        return self.axes.dataLim.intervalx

    def set_data_interval(self, vmin, vmax, ignore=False):
        'set the axis data limits'
        if ignore:
            self.axes.dataLim.intervalx = vmin, vmax
        else:
            Vmin, Vmax = self.get_data_interval()
            self.axes.dataLim.intervalx = min(vmin, Vmin), max(vmax, Vmax)
        self.stale = True

    def set_default_intervals(self):
        'set the default limits for the axis interval if they are not mutated'
        xmin, xmax = 0., 1.
        dataMutated = self.axes.dataLim.mutatedx()
        viewMutated = self.axes.viewLim.mutatedx()
        if not dataMutated or not viewMutated:
            if self.converter is not None:
                info = self.converter.axisinfo(self.units, self)
                if info.default_limits is not None:
                    valmin, valmax = info.default_limits
                    xmin = self.converter.convert(valmin, self.units, self)
                    xmax = self.converter.convert(valmax, self.units, self)
            if not dataMutated:
                self.axes.dataLim.intervalx = xmin, xmax
            if not viewMutated:
                self.axes.viewLim.intervalx = xmin, xmax
        self.stale = True

    def get_tick_space(self):
        (x0, _), (x1, _) = self.axes.transAxes.transform([[0, 0], [1, 0]])
        length = (x1 - x0) * 72 / self.axes.figure.dpi
        # There is a heuristic here that the aspect ratio of tick text
        # is no more than 3:1
        size = self.major.get_labelsize() * 3
        if size > 0:
            return int(np.floor(length / size))
        else:
            return 2**31 - 1


class YAxis(Axis):
    __name__ = 'yaxis'
    axis_name = 'y'
    _tick_collection_class = YTickCollection

    def contains(self, mouseevent):
        """Test whether the mouse event occurred in the y axis.

        Returns *True* | *False*
        """
        if callable(self._contains):
            return self._contains(self, mouseevent)

        x, y = mouseevent.x, mouseevent.y
        try:
            trans = self.axes.transAxes.inverted()
            xaxes, yaxes = trans.transform_point((x, y))
        except ValueError:
            return False, {}
        l, b = self.axes.transAxes.transform_point((0, 0))
        r, t = self.axes.transAxes.transform_point((1, 1))
        inaxis = 0 <= yaxes <= 1 and (
            l - self.pickradius < x < l or
            r < x < r + self.pickradius)
        return inaxis, {}

    def _get_label(self):
        # x in display coords (updated by _update_label_position)
        # y in axes coords
        label = mtext.Text(x=0, y=0.5,
                           # todo: get the label position
                           fontproperties=font_manager.FontProperties(
                               size=rcParams['axes.labelsize'],
                               weight=rcParams['axes.labelweight']),
                           color=rcParams['axes.labelcolor'],
                           verticalalignment='bottom',
                           horizontalalignment='center',
                           rotation='vertical',
                           rotation_mode='anchor')
        label.set_transform(mtransforms.blended_transform_factory(
            mtransforms.IdentityTransform(), self.axes.transAxes))

        self._set_artist_props(label)
        self.label_position = 'left'
        return label

    def _get_offset_text(self):
        # x in display coords, y in axes coords (to be updated at draw time)
        offsetText = mtext.Text(x=0, y=0.5,
                                fontproperties=font_manager.FontProperties(
                                    size=rcParams['ytick.labelsize']
                                ),
                                color=rcParams['ytick.color'],
                                verticalalignment='baseline',
                                horizontalalignment='left')
        offsetText.set_transform(mtransforms.blended_transform_factory(
            self.axes.transAxes, mtransforms.IdentityTransform())
        )
        self._set_artist_props(offsetText)
        self.offset_text_position = 'left'
        return offsetText

    def _get_pixel_distance_along_axis(self, where, perturb):
        """
        Returns the amount, in data coordinates, that a single pixel
        corresponds to in the locality given by *where*, which is also given
        in data coordinates, and is a y coordinate.

        *perturb* is the amount to perturb the pixel.  Usually +0.5 or -0.5.

        Implementing this routine for an axis is optional; if present, it will
        ensure that no ticks are lost due to round-off at the extreme ends of
        an axis.
        """

        #
        # first figure out the pixel location of the "where" point.  We use
        # 1e-10 for the x point, so that we remain compatible with log axes.

        # transformation from data coords to display coords
        trans = self.axes.transData
        # transformation from display coords to data coords
        transinv = trans.inverted()
        pix = trans.transform_point((1e-10, where))
        # perturb the pixel
        ptp = transinv.transform_point((pix[0], pix[1] + perturb))
        dy = abs(ptp[1] - where)
        return dy

    def set_label_position(self, position):
        """
        Set the label position (left or right)

        ACCEPTS: [ 'left' | 'right' ]
        """
        self.label.set_rotation_mode('anchor')
        self.label.set_horizontalalignment('center')
        if position == 'left':
            self.label.set_verticalalignment('bottom')
        elif position == 'right':
            self.label.set_verticalalignment('top')
        else:
            raise ValueError("Position accepts only 'left' or 'right'")
        self.label_position = position
        self.stale = True

    def _update_offset_text_position(self, bboxes, bboxes2):
        """
        Update the offset_text position based on the sequence of bounding
        boxes of all the ticklabels
        """
        x, y = self.offsetText.get_position()
        top = self.axes.bbox.ymax
        self.offsetText.set_position(
            (x, top + self.OFFSETTEXTPAD * self.figure.dpi / 72)
        )

    def set_offset_position(self, position):
        """
        .. ACCEPTS: [ 'left' | 'right' ]
        """
        x, y = self.offsetText.get_position()
        if position == 'left':
            x = 0
        elif position == 'right':
            x = 1
        else:
            raise ValueError("Position accepts only [ 'left' | 'right' ]")

        self.offsetText.set_ha(position)
        self.offsetText.set_position((x, y))
        self.stale = True

    def get_text_widths(self, renderer):
        bbox, bbox2 = self.get_ticklabel_extents(renderer)
        # MGDTODO: Need a better way to get the pad
        padPixels = self.majorTicks[0].get_pad_pixels()

        left = 0.0
        if bbox.width:
            left += bbox.width + padPixels
        right = 0.0
        if bbox2.width:
            right += bbox2.width + padPixels

        if self.get_label_position() == 'left':
            left += self.label.get_window_extent(renderer).width + padPixels
        else:
            right += self.label.get_window_extent(renderer).width + padPixels
        return left, right

    def set_ticks_position(self, position):
        """
        Set the ticks position (left, right, both, default or none)
        'both' sets the ticks to appear on both positions, but does not
        change the tick labels.  'default' resets the tick positions to
        the default: ticks on both positions, labels at left.  'none'
        can be used if you don't want any ticks. 'none' and 'both'
        affect only the ticks, not the labels.

        ACCEPTS: [ 'left' | 'right' | 'both' | 'default' | 'none' ]
        """
        if position == 'right':
            self.set_tick_params(which='both', right=True, labelright=True,
                                 left=False, labelleft=False)
            self.set_offset_position(position)
        elif position == 'left':
            self.set_tick_params(which='both', right=False, labelright=False,
                                 left=True, labelleft=True)
            self.set_offset_position(position)
        elif position == 'both':
            self.set_tick_params(which='both', right=True,
                                 left=True)
        elif position == 'none':
            self.set_tick_params(which='both', right=False,
                                 left=False)
        elif position == 'default':
            self.set_tick_params(which='both', right=True, labelright=False,
                                 left=True, labelleft=True)
        else:
            raise ValueError("invalid position: %s" % position)
        self.stale = True

    def tick_right(self):
        """
        Move ticks and ticklabels (if present) to the right of the axes.
        """
        label = True
        if 'label1On' in self._major_tick_kw:
            label = (self._major_tick_kw['label1On']
                     or self._major_tick_kw['label2On'])
        self.set_ticks_position('right')
        # if labels were turned off before this was called
        # leave them off
        self.set_tick_params(which='both', labelright=label)

    def tick_left(self):
        """
        Move ticks and ticklabels (if present) to the left of the axes.
        """
        label = True
        if 'label1On' in self._major_tick_kw:
            label = (self._major_tick_kw['label1On']
                     or self._major_tick_kw['label2On'])
        self.set_ticks_position('left')
        # if labels were turned off before this was called
        # leave them off
        self.set_tick_params(which='both', labelleft=label)

    def get_ticks_position(self):
        """
        Return the ticks position (left, right, both or unknown)
        """
        majt = self.majorTicks[0]
        mT = self.minorTicks[0]

        majorRight = ((not majt.tick1On) and majt.tick2On and
                      (not majt.label1On) and majt.label2On)
        minorRight = ((not mT.tick1On) and mT.tick2On and
                      (not mT.label1On) and mT.label2On)
        if majorRight and minorRight:
            return 'right'

        majorLeft = (majt.tick1On and (not majt.tick2On) and
                     majt.label1On and (not majt.label2On))
        minorLeft = (mT.tick1On and (not mT.tick2On) and
                     mT.label1On and (not mT.label2On))
        if majorLeft and minorLeft:
            return 'left'

        majorDefault = (majt.tick1On and majt.tick2On and
                        majt.label1On and (not majt.label2On))
        minorDefault = (mT.tick1On and mT.tick2On and
                        mT.label1On and (not mT.label2On))
        if majorDefault and minorDefault:
            return 'default'

        return 'unknown'

    def get_view_interval(self):
        'return the Interval instance for this axis view limits'
        return self.axes.viewLim.intervaly

    def set_view_interval(self, vmin, vmax, ignore=False):
        """
        If *ignore* is *False*, the order of vmin, vmax
        does not matter; the original axis orientation will
        be preserved. In addition, the view limits can be
        expanded, but will not be reduced.  This method is
        for mpl internal use; for normal use, see
        :meth:`~matplotlib.axes.Axes.set_ylim`.

        """
        if ignore:
            self.axes.viewLim.intervaly = vmin, vmax
        else:
            Vmin, Vmax = self.get_view_interval()
            if Vmin < Vmax:
                self.axes.viewLim.intervaly = (min(vmin, vmax, Vmin),
                                               max(vmin, vmax, Vmax))
            else:
                self.axes.viewLim.intervaly = (max(vmin, vmax, Vmin),
                                               min(vmin, vmax, Vmax))
        self.stale = True

    def get_minpos(self):
        return self.axes.dataLim.minposy

    def get_data_interval(self):
        'return the Interval instance for this axis data limits'
        return self.axes.dataLim.intervaly

    def set_data_interval(self, vmin, vmax, ignore=False):
        'set the axis data limits'
        if ignore:
            self.axes.dataLim.intervaly = vmin, vmax
        else:
            Vmin, Vmax = self.get_data_interval()
            self.axes.dataLim.intervaly = min(vmin, Vmin), max(vmax, Vmax)
        self.stale = True

    def set_default_intervals(self):
        'set the default limits for the axis interval if they are not mutated'
        ymin, ymax = 0., 1.
        dataMutated = self.axes.dataLim.mutatedy()
        viewMutated = self.axes.viewLim.mutatedy()
        if not dataMutated or not viewMutated:
            if self.converter is not None:
                info = self.converter.axisinfo(self.units, self)
                if info.default_limits is not None:
                    valmin, valmax = info.default_limits
                    ymin = self.converter.convert(valmin, self.units, self)
                    ymax = self.converter.convert(valmax, self.units, self)
            if not dataMutated:
                self.axes.dataLim.intervaly = ymin, ymax
            if not viewMutated:
                self.axes.viewLim.intervaly = ymin, ymax
        self.stale = True

    def get_tick_space(self):
        (_, y0), (_, y1) = self.axes.transAxes.transform([[0, 0], [0, 1]])
        length = (y1 - y0) * 72 / self.axes.figure.dpi
        # Having a spacing of at least 2 just looks good.
        size = self.major.get_labelsize() * 2
        if size > 0:
            return int(np.floor(length / size))
        else:
            return 2**31 - 1
