""" LinearRegionItem with context menu.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg


class AxisRegionItem(pg.LinearRegionItem):
    """ LinearRegionItem with context menu.
    
    self.sigRegionChangeFinished is emitted when the item is moved or resized.
    """

    def __init__(self, *args, **kwargs):
        if 'orientation' not in kwargs:
            kwargs['orientation'] = 'vertical'
        if 'brush' not in kwargs:
            kwargs['brush'] = pg.mkBrush(QColor(237, 135, 131, 51))
        if 'pen' not in kwargs:
            kwargs['pen'] = pg.mkPen(QColor(237, 135, 131), width=1)
        if 'swapMode' not in kwargs:
            kwargs['swapMode'] = 'push'
        pg.LinearRegionItem.__init__(self, *args, **kwargs)

        self.setZValue(11)
    
    def isMovable(self):
        return self.movable
    
    def setIsMovable(self, movable: bool):
        self.setMovable(movable)
    
    def mouseClickEvent(self, event):
        if event.button() == Qt.RightButton:
            if self.boundingRect().contains(event.pos()):
                if self.raiseContextMenu(event):
                    event.accept()
    
    def raiseContextMenu(self, event):
        menu = self.getContextMenus(event)
        pos = event.screenPos()
        menu.popup(QPoint(int(pos.x()), int(pos.y())))
        return True
    
    def getContextMenus(self, event=None):
        self._thisItemMenu = QMenu(self.__class__.__name__)
        self._thisItemMenu.addAction('Edit', self.editDialog)
        self._thisItemMenu.addSeparator()
        self._thisItemMenu.addAction('Hide', lambda: self.setVisible(False))
        self._thisItemMenu.addSeparator()
        self._thisItemMenu.addAction('Delete', lambda: self.getViewBox().deleteItem(self))

        self.menu = QMenu()
        self.menu.addMenu(self._thisItemMenu)

        # Let the scene add on to the end of our context menu (this is optional)
        self.menu.addSection('View')
        self.menu = self.scene().addParentContextMenus(self, self.menu, event)
        return self.menu
    
    def editDialog(self):
        dlg = QDialog(self.getViewWidget())
        dlg.setWindowTitle('Axis Region')
        form = QFormLayout(dlg)

        limits = sorted(self.getRegion())
        minEdit = QLineEdit(f'{limits[0]:.6f}')
        maxEdit = QLineEdit(f'{limits[1]:.6f}')
        form.addRow('Min', minEdit)
        form.addRow('Max', maxEdit)

        moveableCheckBox = QCheckBox()
        moveableCheckBox.setChecked(self.isMovable())
        form.addRow('Moveable', moveableCheckBox)

        btns = QDialogButtonBox()
        btns.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)

        dlg.move(QCursor.pos())
        dlg.setWindowModality(Qt.ApplicationModal)
        if dlg.exec() != QDialog.Accepted:
            return
        
        limits = sorted([float(minEdit.text()), float(maxEdit.text())])
        self.setRegion(limits)
        
        self.setIsMovable(moveableCheckBox.isChecked())


class XAxisRegionItem(AxisRegionItem):
    """ Vertical AxisRegionItem for x-axis ROI. """

    def __init__(self, *args, **kwargs):
        kwargs['orientation'] = 'vertical'
        AxisRegionItem.__init__(self, *args, **kwargs)


class YAxisRegionItem(AxisRegionItem):
    """ Horizontal AxisRegionItem for y-axis ROI. """

    def __init__(self, *args, **kwargs):
        kwargs['orientation'] = 'horizontal'
        AxisRegionItem.__init__(self, *args, **kwargs)
