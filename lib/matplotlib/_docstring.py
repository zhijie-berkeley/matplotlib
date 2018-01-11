import inspect
import re
from string import Formatter
import sys
import pydoc
import textwrap

from matplotlib import artist


def interpolate(mapping=None):
    """
    Interpolate a function's docstring using `str.format`-style syntax.

    After ::

        @interpolate(mapping)
        def func(): "..."

    in ``func``'s docstring, ``{...}`` elements are replaced by their values,
    taken from the argument mapping, the globals dictionary, or trying to
    resolve dotted names by import and attribute access.

    More specifically, ``{...}`` elements can *only* be preceded by whitespace
    on their line, and the replacement string is first passed through
    `inspect.cleandoc`, then fully indented by the amount of whitespace that
    precedes the ``{...}`` element.

    The ``!P`` converter (``{foo!P}``) can be used to interpolate the
    properties of ``foo`` (as returned by `~.kwdoc`).
    """
    if mapping is None:
        mapping = {}
    def decorator(func):
        func.__uninterpolated_doc__ = func.__doc__
        if func.__doc__ is not None:  # is None under python -OO.
            func.__doc__ = _Formatter().format(
                func.__doc__, **dict(mapping, **sys._getframe(1).f_globals))
        return func
    return decorator


def reinterpolate(orig_func, mapping, func=None):
    def decorator(func):
        if func.__doc__ is not None:
            raise ValueError(
                "reinterpolate unconditionally overwrites the docstring")
        orig_fmt = orig_func.__uninterpolated_doc__
        if orig_fmt is not None:
            func.__doc__ = _Formatter().format(
                orig_fmt, **dict(mapping, **sys._getframe(1).f_globals))
        return func
    return decorator


class _Formatter(Formatter):
    def parse(self, format_string):
        for literal_text, field_name, format_spec, conversion \
                in super().parse(format_string):
            # field_name is None before an escaped brace.
            if field_name is not None:
                if format_spec:
                    raise ValueError(
                        "This custom docstring formatter uses the format_spec "
                        "field to store indentation information")
                # Store indent information in the format_spec field.
                try:
                    last_line, = re.finditer(r"(?m)^ *\Z", literal_text)
                except ValueError:
                    format_spec = "__inline__"
                else:
                    format_spec = last_line.group()
            yield literal_text, field_name, format_spec, conversion

    def get_field(self, field_name, args, kwargs):
        try:
            return super().get_field(field_name, args, kwargs)
        except KeyError:
            return pydoc.locate(field_name), None

    @staticmethod
    def format_field(value, format_spec):
        clean = inspect.cleandoc(value)
        if format_spec == "__inline__":
            if "\n" in clean:
                raise ValueError(
                    "Interpolation fields for multiline values can only be "
                    "preceded by whitespace (which determine the indentation "
                    "of the interpolated string) on their own line")
            return clean
        else:
            # Indent all lines, except the first one (which reuses the indent
            # of the format string).
            return textwrap.indent(inspect.cleandoc(value),
                                   format_spec)[len(format_spec):]

    def convert_field(self, value, conversion):
        if conversion == "P":
            return artist.kwdoc(value)
        else:
            return super().convert_field(value, conversion)
