""" PlotDataItem with custom context menu and style dialog.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
from pyqt_ext import toQColor, GraphStyle, editGraphStyle


class Graph(pg.PlotDataItem):
    """ PlotDataItem with custom context menu and style dialog. """

    sigNameChanged = Signal(str)

    def __init__(self, *args, **kwargs):
        # default style is first MATLAB line color
        if 'pen' not in kwargs:
            kwargs['pen'] = pg.mkPen(QColor(0, 114, 189), width=1)
        if 'symbolPen' not in kwargs:
            kwargs['symbolPen'] = pg.mkPen(QColor(0, 114, 189), width=1)
        if 'symbolBrush' not in kwargs:
            kwargs['symbolBrush'] = pg.mkBrush(QColor(0, 114, 189, 0))
        if 'symbol' not in kwargs:
            kwargs['symbol'] = None
        pg.PlotDataItem.__init__(self, *args, **kwargs)

        self.setZValue(1)
    
    def hasCurve(self):
        pen = pg.mkPen(self.opts['pen'])
        return pen.style() != Qt.PenStyle.NoPen
    
    def hasSymbol(self):
        return 'symbol' in self.opts and self.opts['symbol'] is not None
    
    def shape(self) -> QPainterPath:
        if self.hasCurve():
            return self.curve.shape()
        elif self.hasSymbol():
            return self.scatter.shape()

    def boundingRect(self):
        return self.shape().boundingRect()
    
    def mouseClickEvent(self, event):
        if event.button() == Qt.RightButton:
            if self.hasCurve():
                if self.curve.mouseShape().contains(event.pos()):
                    if self.raiseContextMenu(event):
                        event.accept()
                        return
            if self.hasSymbol():
                if len(self.scatter.pointsAt(event.pos())) > 0:
                    if self.raiseContextMenu(event):
                        event.accept()
                        return
    
    def raiseContextMenu(self, event):
        menu = self.getContextMenus(event)
        pos = event.screenPos()
        menu.popup(QPoint(int(pos.x()), int(pos.y())))
        return True
    
    def getContextMenus(self, event=None):
        name = self.name()
        if name is None:
            name = self.__class__.__name__
        self._thisItemMenu = QMenu(name)
        # self._thisItemMenu.addAction('Rename')
        # self._thisItemMenu.addSeparator()
        self._thisItemMenu.addAction('Style', self.styleDialog)
        # self._thisItemMenu.addSeparator()
        # self._thisItemMenu.addAction('Hide', lambda: self.setVisible(False))
        # self._thisItemMenu.addSeparator()
        # self._thisItemMenu.addAction('Delete', lambda: self.getViewBox().deleteItem(self))

        self.menu = QMenu()
        self.menu.addMenu(self._thisItemMenu)

        # Let the scene add on to the end of our context menu (this is optional)
        self.menu.addSection('View')
        self.menu = self.scene().addParentContextMenus(self, self.menu, event)
        return self.menu
    
    def name(self):
        return self.opts.get('Name', None)
    
    def setName(self, name):
        if name is None:
            del self.opts['Name']
        else:
            self.opts['Name'] = name
        self.sigNameChanged.emit(self.name())
    
    def graphStyle(self) -> GraphStyle:
        style = GraphStyle()

        pen = pg.mkPen(self.opts['pen'])
        symbolPen = pg.mkPen(self.opts['symbolPen'])
        symbolBrush = pg.mkBrush(self.opts['symbolBrush'])

        style.setColor(pen.color())
        style.setLineStyle(pen.style())
        style.setLineWidth(pen.widthF())
        style.setMarker(self.opts.get('symbol', 'none'))
        style.setMarkerSize(self.opts.get('symbolSize', 10))
        style.setMarkerEdgeWidth(symbolPen.widthF())
        markerEdgeColor = symbolPen.color()
        if markerEdgeColor == pen.color():
            markerEdgeColor = 'auto'
        style.setMarkerEdgeColor(markerEdgeColor)
        markerFaceColor = symbolBrush.color()
        if markerFaceColor.alpha() == 0:
            markerFaceColor = 'auto'
        style.setMarkerFaceColor(markerFaceColor)

        return style
    
    def setGraphStyle(self, style: GraphStyle, colorIndex=None):
        # color
        if style.color() == 'auto':
            if colorIndex is not None:
                try:
                    axes = self.getViewBox()
                    colormap = axes.colormap()
                    color = colormap[colorIndex % len(colormap)]
                    color = toQColor(color)
                    colorIndex += 1
                except:
                    color = self.graphStyle().qcolor()
            else:
                color = self.graphStyle().qcolor()
        else:
            color = style.qcolor()

        # line
        lineStyle: Qt.PenStyle = style.lineQtPenStyle()
        lineWidth = style.lineWidth()
        linePen = pg.mkPen(color=color, width=lineWidth, style=lineStyle)
        self.setPen(linePen)

        # marker
        marker = style.marker()
        if marker == 'none':
            marker = None
        self.setSymbol(marker)
        
        markerSize = style.markerSize()
        self.setSymbolSize(markerSize)

        markerEdgeWidth = style.markerEdgeWidth()
        markerEdgeColor = style.markerEdgeColor()
        if markerEdgeColor == 'auto':
            markerEdgeColor = color
        else:
            markerEdgeColor = style.markerEdgeQColor()
        symbolPen = pg.mkPen(color=markerEdgeColor, width=markerEdgeWidth)
        self.setSymbolPen(symbolPen)

        markerFaceColor = style.markerFaceColor()
        if markerFaceColor == 'auto':
            markerFaceColor = markerEdgeColor
            markerFaceColor.setAlpha(0)
        else:
            markerFaceColor = style.markerFaceQColor()
        self.setSymbolBrush(markerFaceColor)
        
        return colorIndex
    
    def styleDialog(self):
        name = self.name()
        if name is None:
            name = self.__class__.__name__
        style: GraphStyle | None = editGraphStyle(self.graphStyle(), parent = self.getViewBox().getViewWidget(), title = name)
        if style is not None:
            self.setGraphStyle(style)

    def setColor(self, color: QColor):
        style: ChartDataStyle = self.graphStyle()
        style.setColor(color)
        self.setGraphStyle(style)
