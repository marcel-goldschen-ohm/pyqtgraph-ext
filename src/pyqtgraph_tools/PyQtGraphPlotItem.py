""" PlotItem with matlab color scheme and CustomViewBox.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
from pyqtgraph_tools import ViewBox


class PlotItem(pg.PlotItem):
    """ PlotItem with matlab color scheme and CustomViewBox. """

    def __init__(self, *args, **kwargs):
        if 'viewBox' not in kwargs:
            kwargs['viewBox'] = ViewBox()
        if 'pen' not in kwargs:
            # MATLAB color scheme
            kwargs['pen'] = pg.mkPen(QColor.fromRgbF(0.15, 0.15, 0.15), width=1)
        pg.PlotItem.__init__(self, *args, **kwargs)

        # MATLAB color scheme
        for axis in ['left', 'bottom', 'right', 'top']:
            self.getAxis(axis).setTextPen(QColor.fromRgbF(0.15, 0.15, 0.15))
