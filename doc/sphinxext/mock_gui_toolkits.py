import sys
from unittest.mock import MagicMock


class MyCairoCffi(MagicMock):
    version_info = (1, 4, 0)


class MyWX(MagicMock):
    class Panel(object):
        pass

    class ToolBar(object):
        pass

    class Frame(object):
        pass


def setup(app):
    sys.modules.update(
        cairocffi=MyCairoCffi(),
        wx=MyWX(),
    )
    return {'parallel_read_safe': True, 'parallel_write_safe': True}
