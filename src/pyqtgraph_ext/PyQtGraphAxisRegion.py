""" LinearRegionItem with context menu.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
from pyqt_ext import ColorButton


class AxisRegion(pg.LinearRegionItem):
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
            kwargs['swapMode'] = 'push'  # keeps label on left side
        pg.LinearRegionItem.__init__(self, *args, **kwargs)

        self.lines[0].sigClicked.connect(self.lineClicked)
        self.lines[1].sigClicked.connect(self.lineClicked)

        self.label: pg.InfLineLabel | None = None

        self._group = None

        # update label position when region is moved or resized
        # TODO: disallow dragging label outside of viewbox
        self.sigRegionChanged.connect(self.updateLabelPosition)

        self.setZValue(11)
    
    def isMovable(self):
        return self.movable
    
    def setIsMovable(self, movable: bool):
        self.setMovable(movable)
    
    def text(self):
        try:
            return self.label.format
        except:
            return ''

    def setText(self, text):
        if text is None or text == '':
            if self.label is not None:
                self.label.setParentItem(None)
                self.label.deleteLater()
            self.label = None
            return
        if self.label is None:
            self.label = pg.InfLineLabel(self.lines[0], text=text, movable=True, position=1, anchors=[(0,0), (0,0)])
            try:
                self.setFontSize(self._label_font_size)
            except:
                pass
        self.label.setFormat(text)
    
    def setFontSize(self, size):
        if self.label is not None:
            font = self.label.textItem.font()
            font.setPointSize(size)
            self.label.textItem.setFont(font)
        else:
            self._label_font_size = size
    
    def group(self) -> str | None:
        return self._group
    
    def setGroup(self, group: str | None):
        self._group = group
    
    def color(self) -> QColor:
        return self.brush.color()
    
    def setColor(self, color: QColor):
        self.brush.setColor(color)
        self.hoverBrush.setColor(color)
    
    def lineColor(self) -> QColor:
        return self.lines[0].pen.color()
    
    def setLineColor(self, color: QColor):
        self.lines[0].pen.setColor(color)
        self.lines[1].pen.setColor(color)
        self.lines[0].hoverPen.setColor(color)
        self.lines[1].hoverPen.setColor(color)
    
    def updateLabelPosition(self):
        if self.label is not None:
            self.label.updatePosition()
    
    def lineClicked(self, line, event):
        if event.button() == Qt.RightButton:
            if self.raiseContextMenu(event):
                event.accept()
    
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
        dlg.setWindowTitle(self.__class__.__name__)
        form = QFormLayout(dlg)
        form.setContentsMargins(5, 5, 5, 5)
        form.setSpacing(5)

        limits = sorted(self.getRegion())
        minEdit = QLineEdit(f'{limits[0]:.6f}')
        maxEdit = QLineEdit(f'{limits[1]:.6f}')
        form.addRow('Min', minEdit)
        form.addRow('Max', maxEdit)

        moveableCheckBox = QCheckBox()
        moveableCheckBox.setChecked(self.isMovable())
        form.addRow('Moveable', moveableCheckBox)

        colorButton = ColorButton(self.color())
        form.addRow('Color', colorButton)

        lineColorButton = ColorButton(self.lineColor())
        form.addRow('Line Color', lineColorButton)

        group = self.group()
        groupEdit = QLineEdit(group if group is not None else '')
        form.addRow('Group', groupEdit)

        text = self.text()
        textEdit = QTextEdit()
        if text is not None and text != '':
            textEdit.setPlainText(text)
        form.addRow('Text', textEdit)

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

        self.setColor(colorButton.color())
        self.setLineColor(lineColorButton.color())

        group = groupEdit.text().strip()
        self.setGroup(group if group != '' else None)

        text = textEdit.toPlainText()
        self.setText(text)


class XAxisRegion(AxisRegion):
    """ Vertical AxisRegionItem for x-axis ROI. """

    def __init__(self, *args, **kwargs):
        kwargs['orientation'] = 'vertical'
        AxisRegion.__init__(self, *args, **kwargs)


class YAxisRegion(AxisRegion):
    """ Horizontal AxisRegionItem for y-axis ROI. """

    def __init__(self, *args, **kwargs):
        kwargs['orientation'] = 'horizontal'
        AxisRegion.__init__(self, *args, **kwargs)
