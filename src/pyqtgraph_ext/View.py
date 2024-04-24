""" ViewBox with matlab color scheme and context menu for drawing ROIs and events.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
from pyqtgraph_ext import XAxisRegion, YAxisRegion


class View(pg.ViewBox):
    """ ViewBox with context menu for drawing ROIs and events. """

    sigStartedDrawingItems = Signal()
    sigItemAdded = Signal(QGraphicsObject)  # emits the newly added QGraphicsObject item
    sigFinishedDrawingItems = Signal()

    def __init__(self, *args, **kwargs):
        pg.ViewBox.__init__(self, *args, **kwargs)

        self._lastMousePressPosInAxesCoords = {}  # dict keys are mouse buttons
        self._drawingItemsOfType = None
        self._itemBeingDrawn = None

        # MATLAB color scheme
        self.setBackgroundColor(QColor(255, 255, 255))

        # colormap (MATLAB lines)
        self._colorIndex = 0
        self._colormap = [
            (  0, 114, 189),
            (217,  83,  25),
            (237, 177,  32),
            (126,  47, 142),
            (119, 172,  48),
            ( 77, 190, 238),
            (162,  20,  47),
        ]
    
    def colormap(self):
        return self._colormap
    
    def setColormap(self, colormap):
        self._colormap = colormap
        self._colorIndex = self._colorIndex % len(self._colormap)
    
    def nextColor(self):
        ncolors = len(self._colormap)
        color = self._colormap[self._colorIndex % ncolors]
        self._colorIndex = (self._colorIndex + 1) % ncolors
        return QColor(*color)
    
    def colorIndex(self):
        return self._colorIndex
    
    def setColorIndex(self, colorIndex):
        self._colorIndex = colorIndex
    
    # def addItem(self, item):
    #     if isinstance(item, Graph):
    #         item.setColor(self.nextColor())
    #     pg.ViewBox.addItem(self, item)
    
    # def initContextMenu(self):
    #     self._ROIsMenu = QMenu("ROIs")
    #     self._ROIsMenu.addAction('Draw X-Axis ROIs (right-click to stop)', lambda: self.startDrawingItemsOfType(XAxisRegion))
    #     # self._ROIsMenu.addAction('Draw Y-Axis ROIs (right-click to stop)', lambda: self.startDrawingItemsOfType(YAxisRegionItem))
    #     self._ROIsMenu.addSeparator()
    #     self._ROIsMenu.addAction("Show All", lambda: self.setVisibilityForItemsOfType(AxisRegion, True))
    #     self._ROIsMenu.addAction("Hide All", lambda: self.setVisibilityForItemsOfType(AxisRegion, False))
    #     self._ROIsMenu.addSeparator()
    #     self._ROIsMenu.addAction("Delete All", lambda: self.deleteItemsOfType(AxisRegion))

    #     # append to default context menu
    #     self.menu.addSection('ROIs')
    #     self.menu.addMenu(self._ROIsMenu)
        
    #     self.menu.addSection('Events')
    #     self.menu.addMenu(self._eventsMenu)

    #     # for appended menus from other objects
    #     self.menu.addSeparator()
    
    def mousePressEvent(self, event):
        # store mouse press position in axes coords
        self._lastMousePressPosInAxesCoords[event.button()] = self.mapSceneToView(self.mapToScene(event.pos()))

        if event.button() == Qt.LeftButton:
            # drawing region?
            if self._drawingItemsOfType in [XAxisRegion, YAxisRegion]:
                startPosInAxesCoords = self._lastMousePressPosInAxesCoords[Qt.LeftButton]
                posInAxesCoords = self.mapSceneToView(self.mapToScene(event.pos()))
                if self._drawingItemsOfType == XAxisRegion:
                    limits = sorted([startPosInAxesCoords.x(), posInAxesCoords.x()])
                    self._itemBeingDrawn = XAxisRegion(values=limits)
                elif self._drawingItemsOfType == YAxisRegion:
                    limits = sorted([startPosInAxesCoords.y(), posInAxesCoords.y()])
                    self._itemBeingDrawn = YAxisRegion(values=limits)
                self.addItem(self._itemBeingDrawn)
                event.accept()
                return
        
        # default if event was not handled above
        pg.ViewBox.mousePressEvent(self, event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # finished drawing region/event?
            if self._drawingItemsOfType is not None and self._itemBeingDrawn is not None:
                self.sigItemAdded.emit(self._itemBeingDrawn)
                self._itemBeingDrawn = None
                event.accept()
                return
        pg.ViewBox.mouseReleaseEvent(self, event)
    
    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            # drawing region?
            if self._drawingItemsOfType in [XAxisRegion, YAxisRegion]:
                startPosInAxesCoords = self._lastMousePressPosInAxesCoords[Qt.LeftButton]
                posInAxesCoords = self.mapSceneToView(self.mapToScene(event.pos()))
                if self._drawingItemsOfType == XAxisRegion:
                    limits = sorted([startPosInAxesCoords.x(), posInAxesCoords.x()])
                elif self._drawingItemsOfType == YAxisRegion:
                    limits = sorted([startPosInAxesCoords.y(), posInAxesCoords.y()])
                self._itemBeingDrawn.setRegion(limits)
                event.accept()
                return
        pg.ViewBox.mouseMoveEvent(self, event)
    
    def listItemsOfType(self, itemType):
        return [item for item in self.allChildren() if isinstance(item, itemType)]
    
    def setVisibilityForItemsOfType(self, itemType, isVisible: bool):
        for item in self.listItemsOfType(itemType):
            item.setVisible(isVisible)
    
    def deleteItemsOfType(self, itemType):
        for item in self.listItemsOfType(itemType):
            self.deleteItem(item)
    
    def deleteItem(self, item):
        self.removeItem(item)
        item.deleteLater()
    
    def startDrawingItemsOfType(self, itemType):
        self._itemBeingDrawn = None
        self._drawingItemsOfType = itemType
        self.sigStartedDrawingItems.emit()
    
    def stopDrawingItems(self):
        self._drawingItemsOfType = None
        self._itemBeingDrawn = None
        self.sigFinishedDrawingItems.emit()


def test_live():
    import numpy as np
    from pyqtgraph_ext import Figure, Graph
    app = QApplication()
    axes = View()
    plot = Figure(viewBox=axes)
    line = Graph(y=np.random.randn(1000))
    plot.addItem(line)
    plot.setWindowTitle('pyqtgraph-tools')
    plot.show()
    app.exec()


if __name__ == '__main__':
    test_live()
