""" PlotWidget with matlab color scheme and CustomPlotItem.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
import numpy as np
import platform
from pyqtgraph_ext import PlotItem


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
    
    def resize_grid(self, rows: int, cols: int, default_item = PlotItem) -> None:
        for row in range(rows):
            for col in range(cols):
                item = self.getItem(row, col)
                print(row, col, item)
                if item is None:
                    item = default_item()
                    print('to add:', item)
                    self.addItem(item, row, col)
        
        # remove extra plots
        if self._grid_layout.count():
            for i in reversed(range(self._grid_layout.count())): 
                item: pg.GraphicsItem = self._grid_layout.itemAt(i)
                print('remove?', item)
                cells = self._graphics_layout.items[item]
                print('cells', cells)
                for row, col in cells:
                    if row >= rows or col >= cols:
                        self.removeItem(item)
                        # del item
                        break
    
    def show_xlabels_for_all_rows(self) -> None:
        rows = self._grid_layout.rowCount()
        cols = self._grid_layout.columnCount()
        for row in range(rows):
            for col in range(cols):
                plot = self.getItem(row, col)
                if issubclass(type(plot), pg.PlotItem):
                    plot.getAxis('bottom').label.show()
    
    def show_xlabels_for_bottom_row_only(self) -> None:
        rows = self._grid_layout.rowCount()
        cols = self._grid_layout.columnCount()
        for row in range(rows):
            for col in range(cols):
                plot = self.getItem(row, col)
                if issubclass(type(plot), pg.PlotItem):
                    if row == rows - 1:
                        plot.getAxis('bottom').label.show()
                    else:
                        plot.getAxis('bottom').label.hide()
    
    def show_xticklabels_for_all_rows(self) -> None:
        rows = self._grid_layout.rowCount()
        cols = self._grid_layout.columnCount()
        for row in range(rows):
            for col in range(cols):
                plot = self.getItem(row, col)
                if issubclass(type(plot), pg.PlotItem):
                    plot.getAxis('bottom').setStyle(showValues=True)
    
    def show_xticklabels_for_bottom_row_only(self) -> None:
        rows = self._grid_layout.rowCount()
        cols = self._grid_layout.columnCount()
        for row in range(rows):
            for col in range(cols):
                plot = self.getItem(row, col)
                if issubclass(type(plot), pg.PlotItem):
                    if row == rows - 1:
                        plot.getAxis('bottom').setStyle(showValues=True)
                    else:
                        plot.getAxis('bottom').setStyle(showValues=False)
    
    def show_ylabels_for_all_columns(self) -> None:
        rows = self._grid_layout.rowCount()
        cols = self._grid_layout.columnCount()
        for row in range(rows):
            for col in range(cols):
                plot = self.getItem(row, col)
                if issubclass(type(plot), pg.PlotItem):
                    plot.getAxis('left').label.show()
    
    def show_ylabels_for_left_column_only(self) -> None:
        rows = self._grid_layout.rowCount()
        cols = self._grid_layout.columnCount()
        for row in range(rows):
            for col in range(cols):
                plot = self.getItem(row, col)
                if issubclass(type(plot), pg.PlotItem):
                    if col == 0:
                        plot.getAxis('left').label.show()
                    else:
                        plot.getAxis('left').label.hide()
    
    def show_yticklabels_for_all_columns(self) -> None:
        rows = self._grid_layout.rowCount()
        cols = self._grid_layout.columnCount()
        for row in range(rows):
            for col in range(cols):
                plot = self.getItem(row, col)
                if issubclass(type(plot), pg.PlotItem):
                    plot.getAxis('left').setStyle(showValues=True)
    
    def show_yticklabels_for_left_column_only(self) -> None:
        rows = self._grid_layout.rowCount()
        cols = self._grid_layout.columnCount()
        for row in range(rows):
            for col in range(cols):
                plot = self.getItem(row, col)
                if issubclass(type(plot), pg.PlotItem):
                    if col == 0:
                        plot.getAxis('left').setStyle(showValues=True)
                    else:
                        plot.getAxis('left').setStyle(showValues=False)
    
    def set_viewbox_relative_sizes(self, row_sizes = None, col_sizes = None) -> None:
        # align view boxes of equal size for all plots
        rows = self._grid_layout.rowCount()
        cols = self._grid_layout.columnCount()
        if rows * cols == 0:
            return
        try:
            if row_sizes is None:
                row_sizes = self._row_sizes
            assert(len(row_sizes) == rows)
            self._row_sizes = np.array(row_sizes) / np.sum(row_sizes)
        except:
            self._row_sizes = np.ones(rows) / rows
        try:
            if col_sizes is None:
                col_sizes = self._col_sizes
            assert(len(col_sizes) == cols)
            self._col_sizes = np.array(col_sizes) / np.sum(col_sizes)
        except:
            self._col_sizes = np.ones(cols) / cols
        marginLeft, marginTop, marginRight, marginBottom = self._grid_layout.getContentsMargins()
        grid_width = self.width() - marginLeft - marginRight
        grid_height = self.height() - marginTop - marginBottom
        nonviewbox_widths = np.zeros((rows, cols))
        nonviewbox_heights = np.zeros((rows, cols))
        for row in range(rows):
            for col in range(cols):
                plot = self.getItem(row, col)
                if issubclass(type(plot), pg.PlotItem):
                    nonviewbox_widths[row, col] = plot.getAxis('left').width() + plot.getAxis('right').width()
                    nonviewbox_heights[row, col] = plot.getAxis('bottom').height() + plot.getAxis('top').height()
        nonviewbox_total_width = np.sum(np.max(nonviewbox_widths, axis=0))
        nonviewbox_total_height = np.sum(np.max(nonviewbox_heights, axis=1))
        viewbox_widths = (grid_width - nonviewbox_total_width) * self._col_sizes
        viewbox_heights = (grid_height - nonviewbox_total_height) * self._row_sizes
        for row in range(rows):
            for col in range(cols):
                plot = self.getItem(row, col)
                plot.setPreferredWidth(viewbox_widths[col] + nonviewbox_widths[row, col])
                plot.setPreferredHeight(viewbox_heights[row] + nonviewbox_heights[row, col])
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        pg.GraphicsLayoutWidget.resizeEvent(self, event)
        try:
            # this fails until the grid layout is initialized
            self.set_viewbox_relative_sizes()
        except:
            pass


def test_live():
    import sys
    app = QApplication(sys.argv)
    grid = PlotGrid()
    for row in range(2):
        for col in range(3):
            plot = PlotItem()
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
    grid.set_viewbox_relative_sizes(row_sizes=[1, 1], col_sizes=[1, 1, 1])
    grid.resize_grid(3, 5)
    grid.show_xlabels_for_bottom_row_only()
    grid.show_ylabels_for_left_column_only()
    grid.show_xticklabels_for_bottom_row_only()
    grid.show_yticklabels_for_left_column_only()
    grid.setWindowTitle('pyqtgraph-tools.PlotGrid')
    grid.show()
    status = app.exec()
    sys.exit(status)


if __name__ == '__main__':
    test_live()
