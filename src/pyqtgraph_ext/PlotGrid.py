""" PlotWidget with matlab color scheme and CustomPlotItem.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
import numpy as np
import platform
from pyqtgraph_ext import Plot


class PlotGrid(pg.GraphicsLayoutWidget):
    """ Grid of PlotItems. """

    def __init__(self, rows=0, cols=0, *args, **kwargs):
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
        
        if rows * cols > 0:
            self.setGrid(rows, cols)
    
    def rowCount(self) -> int:
        return self._grid_layout.rowCount()
            
    def columnCount(self) -> int:
        return self._grid_layout.columnCount()
    
    def clear(self) -> None:
        for item in list(self.items()):
            self.removeItem(item)
    
    def setGrid(self, rows: int, cols: int, plotType = Plot) -> None:
        for row in range(rows):
            for col in range(cols):
                item = self.getItem(row, col)
                if not issubclass(type(item), pg.PlotItem):
                    if item:
                        self.removeItem(item)
                    plot = plotType()
                    self.addItem(plot, row, col)
        for row in reversed(range(rows, self.rowCount())):
            for col in range(self.columnCount()):
                item = self.getItem(row, col)
                if item:
                    self.removeItem(item)
        for col in reversed(range(cols, self.columnCount())):
            for row in range(self.rowCount()):
                item = self.getItem(row, col)
                if item:
                    self.removeItem(item)
        if self.hasRegularLayout():
            self.applyRegularLayout()
    
    def plots(self) -> list[pg.PlotItem]:
        return [item for item in self.items() if issubclass(type(item), pg.PlotItem)]
    
    def hasRegularLayout(self) -> bool:
        return getattr(self, '_hasRegularLayout', False)
    
    def setHasRegularLayout(self, value: bool) -> None:
        self._hasRegularLayout = value
        if value:
            self.applyRegularLayout()
    
    def applyRegularLayout(self) -> None:
        viewWidth = 0
        n = 0
        for col in range(self.columnCount()):
            item = self.getItem(0, col)
            if issubclass(type(item), pg.PlotItem):
                viewWidth += item.getViewBox().width()
                n += 1
        viewWidth /= n
        viewWidth = int(viewWidth)

        viewHeight = 0
        n = 0
        for row in range(self.rowCount()):
            item = self.getItem(row, 0)
            if issubclass(type(item), pg.PlotItem):
                viewHeight += item.getViewBox().height()
                n += 1
        viewHeight /= n
        viewHeight = int(viewHeight)

        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                plot = self.getItem(row, col)
                if issubclass(type(plot), pg.PlotItem):
                    xaxis = plot.getAxis('bottom')
                    yaxis = plot.getAxis('left')
                    plot.setPreferredWidth(viewWidth + yaxis.width() if yaxis.isVisible() else viewWidth)
                    plot.setPreferredHeight(viewHeight + xaxis.height() if xaxis.isVisible() else viewHeight)
    
    def setAxisLabelAndTickVisibility(self, 
        xlabel_rows: list[int] = None,
        xtick_rows: list[int] = None,
        ylabel_columns: list[int] = None,
        ytick_columns: list[int] = None,
    ) -> None:
        # this accounts for any negative indexing
        rows = list(range(self.rowCount()))
        columns = list(range(self.columnCount()))
        xlabel_rows = rows if xlabel_rows is None else [rows[row] for row in xlabel_rows]
        xtick_rows = rows if xtick_rows is None else [rows[row] for row in xtick_rows]
        ylabel_columns = columns if ylabel_columns is None else [columns[col] for col in ylabel_columns]
        ytick_columns = columns if ytick_columns is None else [columns[col] for col in ytick_columns]
        # update axes
        for row in range(self.rowCount()):
            for col in range(self.columnCount()):
                plot = self.getItem(row, col)
                if not issubclass(type(plot), pg.PlotItem):
                    continue
                xaxis = plot.getAxis('bottom')
                yaxis = plot.getAxis('left')
                if row in xlabel_rows:
                    xaxis.label.show()
                else:
                    xaxis.label.hide()
                if col in ylabel_columns:
                    yaxis.label.show()
                else:
                    yaxis.label.hide()
                xaxis.setStyle(showValues=(row in xtick_rows))
                yaxis.setStyle(showValues=(col in ytick_columns))
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        if self.hasRegularLayout():
            self.applyRegularLayout()

def test_live():
    app = QApplication()
    grid = PlotGrid(3, 4)
    grid.setAxisLabelAndTickVisibility(xlabel_rows=[-1], xtick_rows=[-1], ylabel_columns=[0], ytick_columns=[0])
    grid.setHasRegularLayout(True)
    grid.setWindowTitle('pyqtgraph-tools.PlotGrid')
    grid.show()
    QTimer.singleShot(1000, lambda: grid.applyRegularLayout())
    app.exec()


if __name__ == '__main__':
    test_live()
