""" PlotWidget with matlab color scheme and CustomPlotItem.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
import numpy as np
import platform


class PlotGrid(pg.GraphicsLayoutWidget):
    """ Grid of PlotItems. """

    def __init__(self, *args, **kwargs):
        pg.GraphicsLayoutWidget.__init__(self, *args, **kwargs)

        self._graphics_layout: pg.GraphicsLayout = self.ci

        self._grid_layout: QGraphicsGridLayout = self.ci.layout
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setSpacing(0)

        # MATLAB color scheme
        self.setBackground(QColor(240, 240, 240))

        if platform.system() == 'Darwin':
            # Fix error message due to touch events on MacOS trackpad.
            # !!! Warning: This may break touch events on a touch screen or mobile device.
            # See https://bugreports.qt.io/browse/QTBUG-103935
            for view in self.scene().views():
                view.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)
    
    def rowCount(self) -> int:
        return self._grid_layout.rowCount()
            
    def columnCount(self) -> int:
        return self._grid_layout.columnCount()
    
    def applyRegularLayout(self) -> None:
        viewWidth = 0
        for col in range(self.columnCount()):
            viewWidth += self.getItem(0, col).getViewBox().width()
        viewWidth /= self.columnCount()
        viewWidth = int(viewWidth)

        viewHeight = 0
        for row in range(self.rowCount()):
            viewHeight += self.getItem(row, 0).getViewBox().height()
        viewHeight /= self.rowCount()
        viewHeight = int(viewHeight)

        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                plot = self.getItem(row, col)
                xaxis = plot.getAxis('bottom')
                yaxis = plot.getAxis('left')
                plot.setPreferredWidth(viewWidth + yaxis.width() if yaxis.isVisible() else viewWidth)
                plot.setPreferredHeight(viewHeight + xaxis.height() if xaxis.isVisible() else viewHeight)

def test_live():
    from pyqtgraph_ext import Plot
    app = QApplication()
    grid = PlotGrid()
    for row in range(2):
        for col in range(3):
            plot = Plot()
            if col == 0:
                plot.getAxis('left').setLabel('y')
            else:
                plot.getAxis('left').label.hide()
                plot.getAxis('left').setStyle(showValues=False)
            if row == 1:
                plot.getAxis('bottom').setLabel('x')
            else:
                plot.getAxis('bottom').label.hide()
                plot.getAxis('bottom').setStyle(showValues=False)
            grid.addItem(plot, row, col)
    grid.applyRegularLayout()
    grid.setWindowTitle('pyqtgraph-tools.PlotGrid')
    grid.show()
    app.exec()


if __name__ == '__main__':
    test_live()
