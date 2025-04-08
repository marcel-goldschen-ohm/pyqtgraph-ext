""" LinearRegionItem with context menu, optional text label, and style dialog.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
from pyqt_ext.utils import toColorStr, toQColor
from pyqt_ext.widgets import ColorButton, CollapsibleSection


class AxisRegion(pg.LinearRegionItem):
    """ LinearRegionItem with context menu, optional text label, and style dialog.
    
    self.sigRegionChangeFinished is emitted when the item is moved or resized.
    """

    sigRegionDragFinished = Signal(object)
    sigEditingFinished = Signal(object)
    sigRequestDeletion = Signal(object)

    def __init__(self, *args, **kwargs):
        if 'orientation' not in kwargs:
            kwargs['orientation'] = 'vertical'
        if 'brush' not in kwargs:
            kwargs['brush'] = pg.mkBrush(QColor(237, 135, 131, 51))
        if 'hoverBrush' not in kwargs:
            kwargs['hoverBrush'] = pg.mkBrush(QColor(237, 135, 131, 128))
        if 'pen' not in kwargs:
            kwargs['pen'] = pg.mkPen(QColor(237, 135, 131), width=1)
        if 'hoverPen' not in kwargs:
            kwargs['hoverPen'] = pg.mkPen(QColor(255, 0, 0), width=2)
        if 'swapMode' not in kwargs:
            kwargs['swapMode'] = 'push'  # keeps label on left side
        pg.LinearRegionItem.__init__(self, *args, **kwargs)

        self._textLabelItem: pg.InfLineLabel = pg.InfLineLabel(self.lines[0], text='', movable=True, position=1, anchors=[(0,0), (0,0)])
        self._textLabelItem.setVisible(False)
        self.setFontColor(QColor.fromRgbF(0.15, 0.15, 0.15))

        self.lines[0].sigClicked.connect(self.onEdgeClicked)
        self.lines[1].sigClicked.connect(self.onEdgeClicked)

        self._group = ''

        # update label position when region is moved or resized
        # TODO: disallow dragging label outside of viewbox
        self.sigRegionChanged.connect(self.updateLabelPosition)
        # self.sigRegionChangeFinished.connect(lambda self=self: self.storeState())

        self.setZValue(11)
    
    def getState(self, dim: str = None) -> dict:
        """ Return hashable dict for saving and restoring state.
        """
        return {
            'region': self.getRegion() if dim is None else {dim: self.getRegion()},
            'text': self.text(),
            'movable': self.movable,
            'group': self.group(),
            'format': self.getFormat(),
        }
    
    def setState(self, state: dict, dim: str = None):
        """ Restore state from hashable dict.
        """
        for key, value in state.items():
            key = key.lower()
            if key == 'region':
                if isinstance(value, dict):
                    if dim is None:
                        raise KeyError('Dimension must be specified when region is a dict')
                    value = value[dim]
                self.setRegion(value)
            elif key == 'text':
                self.setText(value)
            elif key == 'movable':
                self.setMovable(value)
            elif key == 'group':
                self.setGroup(value)
            elif key == 'format':
                self.setFormat(value)
    
    def getFormat(self) -> dict:
        """ Return hashable dict for saving and restoring state.
        """
        return {
            'facecolor': toColorStr(self.faceColor()),
            'edgecolor': toColorStr(self.edgeColor()),
            'edgewidth': self.edgeWidth(),
            'facehovercolor': toColorStr(self.faceHoverColor()),
            'edgehovercolor': toColorStr(self.edgeHoverColor()),
            'edgehoverwidth': self.edgeHoverWidth(),
            'font': self.font().toString(),
            'fontsize': self.fontSize(),
            'fontcolor': toColorStr(self.fontColor()),
        }
    
    def setFormat(self, state: dict):
        """ Restore state from hashable dict.
        """
        for key, value in state.items():
            key = key.lower()
            if key == 'facecolor':
                self.setFaceColor(toQColor(value))
            elif key == 'edgecolor':
                self.setEdgeColor(toQColor(value))
            elif key == 'edgewidth':
                self.setEdgeWidth(value)
            elif key == 'facehovercolor':
                self.setFaceHoverColor(toQColor(value))
            elif key == 'edgehovercolor':
                self.setEdgeHoverColor(toQColor(value))
            elif key == 'edgehoverwidth':
                self.setEdgeHoverWidth(value)
            elif key == 'font':
                font = QFont()
                font.fromString(value)
                self.setFont(font)
            elif key == 'fontsize':
                self.setFontSize(value)
            elif key == 'fontcolor':
                self.setFontColor(toQColor(value))
    
    def storeState(self):
        dim = getattr(self, '_dim', None)
        self._state = self.getState(dim=dim)
    
    def restoreState(self):
        if not hasattr(self, '_state'):
            raise AttributeError('State has not been stored')
        dim = getattr(self, '_dim', None)
        self.setState(self._state, dim=dim)
    
    # def setRegion(self, rgn):
    #     """ Override default method to avoid emitting sigRegionChangeFinished
    #     which we only want to emit after a drag event.
    #     """
    #     if self.lines[0].value() == rgn[0] and self.lines[1].value() == rgn[1]:
    #         return
    #     self.blockLineSignal = True
    #     self.lines[0].setValue(rgn[0])
    #     # self.blockLineSignal = False
    #     self.lines[1].setValue(rgn[1])
    #     self.blockLineSignal = False
    #     self.lineMoved(0)
    #     self.lineMoved(1)
    #     self.lineMoveFinished()

    def mouseDragEvent(self, ev):
        """ Add new signal for when drag is finished.
        """
        if not self.movable or ev.button() != Qt.MouseButton.LeftButton:
            return
        ev.accept()
        
        if ev.isStart():
            bdp = ev.buttonDownPos()
            self.cursorOffsets = [l.pos() - bdp for l in self.lines]
            self.startPositions = [l.pos() for l in self.lines]
            self.moving = True
            
        if not self.moving:
            return
            
        self.blockLineSignal = True  # only want to update once
        for i, l in enumerate(self.lines):
            l.setPos(self.cursorOffsets[i] + ev.pos())
        self.prepareGeometryChange()
        self.blockLineSignal = False
        
        if ev.isFinish():
            self.moving = False
            self.sigRegionChangeFinished.emit(self)
            self.sigRegionDragFinished.emit(self)
        else:
            self.sigRegionChanged.emit(self)
    
    def group(self):
        return self._group
    
    def setGroup(self, group):
        self._group = group
    
    def faceColor(self) -> QColor:
        return self.brush.color()
    
    def setFaceColor(self, color: QColor):
        self.brush.setColor(color)
    
    def edgePen(self) -> QPen:
        return self.lines[0].pen
    
    def setEdgePen(self, pen: QPen):
        self.lines[0].pen = pen
        self.lines[1].pen = pen
    
    def edgeColor(self) -> QColor:
        return self.lines[0].pen.color()
    
    def setEdgeColor(self, color: QColor):
        self.lines[0].pen.setColor(color)
        self.lines[1].pen.setColor(color)
    
    def edgeWidth(self) -> float:
        return self.lines[0].pen.width()
    
    def setEdgeWidth(self, width: float):
        self.lines[0].pen.setWidth(width)
        self.lines[1].pen.setWidth(width)
    
    def faceHoverColor(self) -> QColor:
        return self.hoverBrush.color()
    
    def setFaceHoverColor(self, color: QColor):
        self.hoverBrush.setColor(color)
    
    def edgeHoverPen(self) -> QPen:
        return self.lines[0].hoverPen
    
    def setEdgeHoverPen(self, pen: QPen):
        self.lines[0].hoverPen = pen
        self.lines[1].hoverPen = pen
    
    def edgeHoverColor(self) -> QColor:
        return self.lines[0].hoverPen.color()
    
    def setEdgeHoverColor(self, color: QColor):
        self.lines[0].hoverPen.setColor(color)
        self.lines[1].hoverPen.setColor(color)
    
    def edgeHoverWidth(self) -> float:
        return self.lines[0].hoverPen.width()
    
    def setEdgeHoverWidth(self, width: float):
        self.lines[0].hoverPen.setWidth(width)
        self.lines[1].hoverPen.setWidth(width)

    def text(self):
        try:
            return self._textLabelItem.format
        except:
            return ''

    def setText(self, text: str):
        self._textLabelItem.setFormat(text)
        self._textLabelItem.setVisible(text != '')
    
    def font(self) -> QFont:
        return self._textLabelItem.textItem.font()
    
    def setFont(self, font: QFont):
        self._textLabelItem.setFont(font)
    
    def fontSize(self) -> int:
        return self._textLabelItem.textItem.font().pointSize()
    
    def setFontSize(self, size):
        font = self._textLabelItem.textItem.font()
        font.setPointSize(size)
        self._textLabelItem.setFont(font)
    
    def fontColor(self) -> QColor:
        return self._textLabelItem.color
    
    def setFontColor(self, color: QColor):
        self._textLabelItem.setColor(color)
    
    def copyFormat(self, other: AxisRegion):
        self.setFormat(other.getFormat())
    
    def updateLabelPosition(self):
        if self._textLabelItem is not None:
            self._textLabelItem.updatePosition()
            pos = self._textLabelItem.orthoPos
            if pos < 0.05:
                self._textLabelItem.setPosition(0.05)
    
    def onEdgeClicked(self, line, event):
        if event.button() == Qt.RightButton:
            if self.raiseContextMenu(event):
                event.accept()
    
    def mouseClickEvent(self, event):
        if event.button() == Qt.RightButton:
            if self.boundingRect().contains(event.pos()):
                if self.raiseContextMenu(event):
                    event.accept()
    
    # def mouseReleaseEvent(self, event):
    #     print('mouseReleaseEvent')
    
    def raiseContextMenu(self, event):
        menu = self.getContextMenus(event)
        pos = event.screenPos()
        menu.popup(QPoint(int(pos.x()), int(pos.y())))
        return True
    
    def getContextMenus(self, event=None):
        self.menu = QMenu()

        self._thisItemMenu = QMenu(self.__class__.__name__)
        self._thisItemMenu.addAction('Edit', lambda: self.editDialog())
        # self._thisItemMenu.addSeparator()
        # self._thisItemMenu.addAction('Hide', lambda: self.setVisible(False))
        self._thisItemMenu.addSeparator()
        self._thisItemMenu.addAction('Delete', lambda: self.sigRequestDeletion.emit(self))
        self.menu.addMenu(self._thisItemMenu)

        # Let the scene add on to the end of our context menu (this is optional)
        self.menu.addSection('View')
        self.menu = self.scene().addParentContextMenus(self, self.menu, event)
        return self.menu
    
    def editDialog(self, parent: QWidget = None):
        editAxisRegion(self, parent=parent)
        self.sigEditingFinished.emit(self)


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


class AxisRegionPanel(QWidget):

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        form = QFormLayout(self)
        form.setContentsMargins(5, 5, 5, 5)
        form.setSpacing(5)

        self._minEdit = QLineEdit()
        self._maxEdit = QLineEdit()
        form.addRow('Min', self._minEdit)
        form.addRow('Max', self._maxEdit)

        self._movableCheckBox = QCheckBox()
        form.addRow('Movable', self._movableCheckBox)

        self._groupEdit = QLineEdit()
        form.addRow('Group', self._groupEdit)

        self._textEdit = QTextEdit()
        form.addRow('Text', self._textEdit)

        self._formatPanel = AxisRegionFormatPanel()
        self._formatPanelWrapperLayout = QVBoxLayout()
        self._formatPanelWrapperLayout.setContentsMargins(0, 0, 0, 0)
        self._formatPanelWrapperLayout.addWidget(self._formatPanel)

        self._formatSection = CollapsibleSection(title='Format')
        self._formatSection.setContentLayout(self._formatPanelWrapperLayout)
        form.addRow(self._formatSection)

        # default settings
        self.setState(AxisRegion().getState())
    
    def getState(self):
        state = {}

        if self._minEdit.text() != '' and self._maxEdit.text() != '':
            state['region'] = tuple(sorted([float(self._minEdit.text()), float(self._maxEdit.text())]))

        if self._movableCheckBox.checkState() != Qt.CheckState.PartiallyChecked:
            state['movable'] = self._movableCheckBox.isChecked()
        
        state['group'] = self._groupEdit.text()
        
        state['text'] = self._textEdit.toPlainText()

        state['format'] = self._formatPanel.getFormat()

        return state

    def setState(self, state):
        for key, value in state.items():
            key = key.lower()
            if key == 'region':
                self._minEdit.setText(f'{value[0]:.6f}')
                self._maxEdit.setText(f'{value[1]:.6f}')
            elif key == 'movable':
                self._movableCheckBox.setChecked(value)
            elif key == 'group':
                self._groupEdit.setText(str(value))
            elif key == 'text':
                self._textEdit.setPlainText(value)
            elif key == 'format':
                self._formatPanel.setFormat(value)


class AxisRegionFormatPanel(QWidget):

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)

        self._faceColorButton = ColorButton()
        self._edgeColorButton = ColorButton()
        self._edgeWidthSpinBox = QDoubleSpinBox()

        self._faceHoverColorButton = ColorButton()
        self._edgeHoverColorButton = ColorButton()
        self._edgeHoverWidthSpinBox = QDoubleSpinBox()

        self._fontColorButton = ColorButton()
        self._fontSizeSpinBox = QDoubleSpinBox()

        self._formatLayout = QFormLayout()
        self._formatLayout.setContentsMargins(5, 5, 5, 5)
        self._formatLayout.setSpacing(5)
        self._formatLayout.addRow('Face Color', self._faceColorButton)
        self._formatLayout.addRow('Edge Color', self._edgeColorButton)
        self._formatLayout.addRow('Edge Width', self._edgeWidthSpinBox)
        self._formatLayout.addRow('Font Color', self._fontColorButton)
        self._formatLayout.addRow('Font Size', self._fontSizeSpinBox)

        self._hoverLayout = QFormLayout()
        self._hoverLayout.setContentsMargins(5, 5, 5, 5)
        self._hoverLayout.setSpacing(5)
        self._hoverLayout.addRow('Face Hover Color', self._faceHoverColorButton)
        self._hoverLayout.addRow('Edge Hover Color', self._edgeHoverColorButton)
        self._hoverLayout.addRow('Edge Hover Width', self._edgeHoverWidthSpinBox)

        self._hoverLayoutWrapper = QVBoxLayout()
        self._hoverLayoutWrapper.addLayout(self._hoverLayout)
        self._hoverLayoutWrapper.addStretch()

        self._formatLayoutWrapper = QHBoxLayout()
        self._formatLayoutWrapper.addLayout(self._formatLayout)
        self._formatLayoutWrapper.addLayout(self._hoverLayoutWrapper)

        self.setLayout(self._formatLayoutWrapper)

        # default settings
        self.setFormat(AxisRegion().getFormat())
    
    def getFormat(self):
        fmt = {}

        faceColor = self._faceColorButton.color()
        edgeColor = self._edgeColorButton.color()
        edgeWidth = self._edgeWidthSpinBox.value()
        fontSize = self._fontSizeSpinBox.value()
        fontColor = self._fontColorButton.color()
        faceHoverColor = self._faceHoverColorButton.color()
        edgeHoverColor = self._edgeHoverColorButton.color()
        edgeHoverWidth = self._edgeHoverWidthSpinBox.value()

        if faceColor is not None:
            fmt['facecolor'] = toColorStr(faceColor)
        if edgeColor is not None:
            fmt['edgecolor'] = toColorStr(edgeColor)
        if edgeWidth > 0:
            fmt['edgewidth'] = edgeWidth
        if fontSize > 0:
            fmt['fontsize'] = fontSize
        if fontColor is not None:
            fmt['fontcolor'] = toColorStr(fontColor)
        if faceHoverColor is not None:
            fmt['facehovercolor'] = toColorStr(faceHoverColor)
        if edgeHoverColor is not None:
            fmt['edgehovercolor'] = toColorStr(edgeHoverColor)
        if edgeHoverWidth > 0:
            fmt['edgehoverwidth'] = edgeHoverWidth

        return fmt

    def setFormat(self, fmt: dict):
        for key, value in fmt.items():
            key = key.lower()
            if key == 'facecolor':
                self._faceColorButton.setColor(toQColor(value))
            elif key == 'edgecolor':
                self._edgeColorButton.setColor(toQColor(value))
            elif key == 'edgewidth':
                self._edgeWidthSpinBox.setValue(value)
            elif key == 'facehovercolor':
                self._faceHoverColorButton.setColor(toQColor(value))
            elif key == 'edgehovercolor':
                self._edgeHoverColorButton.setColor(toQColor(value))
            elif key == 'edgehoverwidth':
                self._edgeHoverWidthSpinBox.setValue(value)
            elif key == 'fontsize':
                self._fontSizeSpinBox.setValue(value)
            elif key == 'fontcolor':
                self._fontColorButton.setColor(toQColor(value))


def editAxisRegion(region: AxisRegion = None, parent: QWidget = None, title: str = None) -> dict | None:
    if region is None:
        region = AxisRegion()
    
    panel = AxisRegionPanel()
    panel.layout().setContentsMargins(0, 0, 0, 0)
    panel.setState(region.getState())

    dlg = QDialog(parent)
    vbox = QVBoxLayout(dlg)
    vbox.addWidget(panel)

    btns = QDialogButtonBox()
    btns.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
    btns.accepted.connect(dlg.accept)
    btns.rejected.connect(dlg.reject)
    vbox.addWidget(btns)
    vbox.addStretch()

    if title is not None:
        dlg.setWindowTitle(title)
    dlg.setWindowModality(Qt.ApplicationModal)
    
    if dlg.exec() != QDialog.Accepted:
        return
    
    region.setState(panel.getState())

    return region.getState()


def formatAxisRegion(region: AxisRegion = None, parent: QWidget = None, title: str = None) -> dict | None:
    if region is None:
        region = AxisRegion()
    
    panel = AxisRegionFormatPanel()
    panel.layout().setContentsMargins(0, 0, 0, 0)
    panel.setFormat(region.getFormat())

    dlg = QDialog(parent)
    vbox = QVBoxLayout(dlg)
    vbox.addWidget(panel)

    btns = QDialogButtonBox()
    btns.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
    btns.accepted.connect(dlg.accept)
    btns.rejected.connect(dlg.reject)
    vbox.addWidget(btns)
    vbox.addStretch()

    if title is not None:
        dlg.setWindowTitle(title)
    dlg.setWindowModality(Qt.ApplicationModal)
    
    if dlg.exec() != QDialog.Accepted:
        return
    
    region.setFormat(panel.getFormat())

    return region.getFormat()


# def editMultipleAxisRegions(regions: list[AxisRegion], parent: QWidget = None, title: str = None):
#     panel = AxisRegionPanel()
#     panel.layout().setContentsMargins(0, 0, 0, 0)
#     states = [region.getState() for region in regions]
#     panel.setState(states[0])
#     for state in states[1:]:
#         if state['region'] != states[0]['region']:
#             self._minEdit.setText('')
#             self._maxEdit.setText('')
#         if state['movable'] != states[0]['movable']:
#             self._movableCheckBox.setCheckState(Qt.PartiallyChecked)
#         if state['text'] != states[0]['text']:
#             self._textEdit.setPlainText('')
#         for key in state['format']:
#             if key not in states[0]['format'] or state['format'][key] != states[0]['format'][key]:
#                 pass
#     panel.setState(shared_state)

#     dlg = QDialog(parent)
#     vbox = QVBoxLayout(dlg)
#     vbox.addWidget(panel)

#     btns = QDialogButtonBox()
#     btns.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
#     btns.accepted.connect(dlg.accept)
#     btns.rejected.connect(dlg.reject)
#     vbox.addWidget(btns)
#     vbox.addStretch()

#     if title is not None:
#         dlg.setWindowTitle(title)
#     dlg.setWindowModality(Qt.ApplicationModal)
    
#     if dlg.exec() != QDialog.Accepted:
#         return


def test_live():
    app = QApplication()

    ui = AxisRegionPanel()
    ui.show()

    app.exec()

if __name__ == '__main__':
    test_live()