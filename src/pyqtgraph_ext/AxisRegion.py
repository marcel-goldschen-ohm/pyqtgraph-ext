""" LinearRegionItem with context menu.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
from pyqt_ext.utils import toColorStr, toQColor
from pyqt_ext.widgets import ColorButton


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

        self._textLabelItem: pg.InfLineLabel = pg.InfLineLabel(self.lines[0], text='', movable=True, position=1, anchors=[(0,0), (0,0)])
        self._textLabelItem.setVisible(False)

        self.lines[0].sigClicked.connect(self.edgeLineClicked)
        self.lines[1].sigClicked.connect(self.edgeLineClicked)

        # update label position when region is moved or resized
        # TODO: disallow dragging label outside of viewbox
        self.sigRegionChanged.connect(self.updateLabelPosition)
        self.sigRegionChangeFinished.connect(lambda self=self: self.toDict())

        self.setZValue(11)
    
    def isMovable(self):
        return self.movable
    
    def setIsMovable(self, movable: bool):
        self.setMovable(movable)
    
    def text(self):
        try:
            return self._textLabelItem.format
        except Exception:
            return ''

    def setText(self, text: str):
        self._textLabelItem.setFormat(text)
        self._textLabelItem.setVisible(text != '')
    
    def fontSize(self) -> int:
        return self._textLabelItem.textItem.font().pointSize()
    
    def setFontSize(self, size):
        font = self._textLabelItem.textItem.font()
        font.setPointSize(size)
        self._textLabelItem.textItem.setFont(font)
    
    def color(self) -> QColor:
        return self.brush.color()
    
    def setColor(self, color: QColor):
        self.brush.setColor(color)
        self.hoverBrush.setColor(color)
    
    def edgeLineColor(self) -> QColor:
        return self.lines[0].pen.color()
    
    def setEdgeLineColor(self, color: QColor):
        self.lines[0].pen.setColor(color)
        self.lines[1].pen.setColor(color)
        self.lines[0].hoverPen.setColor(color)
        self.lines[1].hoverPen.setColor(color)
    
    def edgeLineWidth(self) -> float:
        return self.lines[0].pen.width()
    
    def setEdgeLineWidth(self, width: float):
        self.lines[0].pen.setWidth(width)
        self.lines[1].pen.setWidth(width)
        self.lines[0].hoverPen.setWidth(width)
        self.lines[1].hoverPen.setWidth(width)
    
    def updateLabelPosition(self):
        if self._textLabelItem is not None:
            self._textLabelItem.updatePosition()
            pos = self._textLabelItem.orthoPos
            if pos < 0.05:
                self._textLabelItem.setPosition(0.05)
    
    def edgeLineClicked(self, line, event):
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
        self.menu = QMenu()

        self._thisItemMenu = QMenu(self.__class__.__name__)
        self._thisItemMenu.addAction('Edit', lambda: self.editDialog())
        # the XAxisRegionTreeView manager will handle this...
        # self._thisItemMenu.addSeparator()
        # self._thisItemMenu.addAction('Hide', lambda: self.setVisible(False))
        # self._thisItemMenu.addSeparator()
        # self._thisItemMenu.addAction('Delete', lambda: self.getViewBox().deleteItem(self))
        self.menu.addMenu(self._thisItemMenu)

        # Let the scene add on to the end of our context menu (this is optional)
        self.menu.addSection('View')
        self.menu = self.scene().addParentContextMenus(self, self.menu, event)
        return self.menu
    
    def editDialog(self, parent: QWidget = None):
        if parent is None:
            parent = self.getViewWidget()
        dlg = QDialog(parent)
        dlg.setWindowTitle(self.__class__.__name__)
        form = QFormLayout(dlg)
        form.setContentsMargins(5, 5, 5, 5)
        form.setSpacing(5)

        limits = sorted(self.getRegion())
        minEdit = QLineEdit(f'{limits[0]:.6f}')
        maxEdit = QLineEdit(f'{limits[1]:.6f}')
        form.addRow('Min', minEdit)
        form.addRow('Max', maxEdit)

        movableCheckBox = QCheckBox()
        movableCheckBox.setChecked(self.isMovable())
        form.addRow('Movable', movableCheckBox)

        colorButton = ColorButton(self.color())
        form.addRow('Color', colorButton)

        lineColorButton = ColorButton(self.edgeLineColor())
        form.addRow('Line Color', lineColorButton)

        lineWidthSpinBox = QDoubleSpinBox()
        lineWidthSpinBox.setValue(self.edgeLineWidth())
        form.addRow('Line Width', lineWidthSpinBox)

        # label = self.label()
        # labelEdit = QLineEdit(label if label is not None else '')
        # form.addRow('Label', labelEdit)

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
        
        self.setIsMovable(movableCheckBox.isChecked())

        self.setColor(colorButton.color())
        self.setEdgeLineColor(lineColorButton.color())
        self.setEdgeLineWidth(lineWidthSpinBox.value())

        # label = labelEdit.text().strip()
        # self.setLabel(label if label != '' else None)

        text = textEdit.toPlainText()
        self.setText(text)
        
        # do this last so that the sigRegionChanged signal can be used for all things in this dialog
        limits = sorted([float(minEdit.text()), float(maxEdit.text())])
        self.setRegion(limits)

        # in case region was unchanged, we still want this signal to be emitted
        self.sigRegionChangeFinished.emit(self)
    
    def toDict(self, data: dict = None, dim: str = None):
        if dim is None:
            dim = getattr(self, '_dim', None)
        if data is None:
            if not hasattr(self, '_data'):
                self._data = {}
            data = self._data
        lims = list(sorted(self.getRegion()))
        if dim is not None:
            if 'region' not in data:
                data['region'] = {}
            data['region'][dim] = lims
        # elif 'region' in data and isinstance(data['region'], dict) and len(data['region']) > 0:
        #     dim = list(data['region'].keys())[0]
        #     data['region'][dim] = lims
        else:
            data['region'] = lims
        data['text'] = self.text()
        data['movable'] = self.isMovable()
        data['color'] = toColorStr(self.color())
        data['edgecolor'] = toColorStr(self.edgeLineColor())
        data['edgewidth'] = self.edgeLineWidth()
    
    def fromDict(self, data: dict, dim: str = None):
        if dim is None:
            dim = getattr(self, '_dim', None)
        if 'region' in data:
            if isinstance(data['region'], dict):
                if dim is not None and dim in data['region']:
                    self.setRegion(data['region'][dim])
            elif isinstance(data['region'], list):
                self.setRegion(data['region'])
        self.setText(data.get('text', ''))
        self.setIsMovable(data.get('movable', True))
        if 'color' in data:
            self.setColor(toQColor(data['color']))
        if 'edgecolor' in data:
            self.setEdgeLineColor(toQColor(data['edgecolor']))
        if 'edgewidth' in data:
            self.setEdgeLineWidth(data['edgewidth'])
        self._data = data


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
