""" PlotItem with matlab color scheme and CustomViewBox.
"""

from __future__ import annotations
from qtpy.QtGui import QColor
import pyqtgraph as pg
from pyqtgraph_ext import View


class Plot(pg.PlotItem):
    """ PlotItem with matlab color scheme and custom ViewBox. """

    def __init__(self, *args, **kwargs):
        if 'viewBox' not in kwargs:
            kwargs['viewBox'] = View()
        if 'pen' not in kwargs:
            # MATLAB color scheme
            kwargs['pen'] = pg.mkPen(QColor.fromRgbF(0.15, 0.15, 0.15), width=1)
        pg.PlotItem.__init__(self, *args, **kwargs)

        # MATLAB color scheme
        for axis in ['left', 'bottom', 'right', 'top']:
            axis_item = self.getAxis(axis)
            if axis_item is not None:
                axis_item.setTextPen(QColor.fromRgbF(0.15, 0.15, 0.15))
