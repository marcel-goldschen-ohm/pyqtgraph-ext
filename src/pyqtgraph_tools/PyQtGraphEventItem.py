""" AxisRegionItem with custom context menu and label for an event.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
from pyqtgraph_tools import AxisRegionItem


class EventItem(AxisRegionItem):
    """ AxisRegionItem with context menu and label for an event.
    
    self.sigRegionChangeFinished is emitted when the item is moved or resized.
    """

    def __init__(self, *args, **kwargs):
        kwargs['orientation'] = 'vertical'
        if 'brush' not in kwargs:
            kwargs['brush'] = pg.mkBrush(QColor.fromRgbF(0.0, 0.447, 0.741, 0.2))
        if 'pen' not in kwargs:
            kwargs['pen'] = pg.mkPen(QColor.fromRgbF(0.0, 0.447, 0.741), width=1)
        kwargs['swapMode'] = 'push'  # keep label on left side
        AxisRegionItem.__init__(self, *args, **kwargs)

        self.setZValue(10)
        
        self.lines[0].label = EventLabel(self.lines[0], text='Event', movable=True, position=1, anchors=[(0,0), (0,0)])
        self.lines[0].label.setColor((0, 0, 0, 128))
        self.lines[0].label.eventItem = self  # for context menu

        # update text position when event region is moved or resized
        self.sigRegionChanged.connect(self.lines[0].label.updatePosition)
    
    def text(self):
        return self.lines[0].label.format

    def setText(self, text):
        self.lines[0].label.setFormat(text)
    
    def editDialog(self):
        dlg = QDialog(self.getViewWidget())
        dlg.setWindowTitle('Event')
        form = QFormLayout(dlg)

        start, stop = self.getRegion()
        startEdit = QLineEdit(f'{start:.6f}')
        if stop == start:
            stopEdit = QLineEdit()
        else:
            stopEdit = QLineEdit(f'{stop:.6f}')
        form.addRow('Start', startEdit)
        form.addRow('Stop', stopEdit)

        moveableCheckBox = QCheckBox()
        moveableCheckBox.setChecked(self.isMovable())
        form.addRow('Moveable', moveableCheckBox)

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

        text = textEdit.toPlainText()
        self.setText(text)
        
        start = float(startEdit.text())
        stop = float(stopEdit.text()) if stopEdit.text() != '' else start
        self.setRegion(sorted([start, stop]))

        self.setIsMovable(moveableCheckBox.isChecked())


class EventLabel(pg.InfLineLabel):
    """ InfLineLabel with context menu for event.
    
    Access to context menu for when the event has zero duration.
    """

    def __init__(self, *args, **kwargs):
        pg.InfLineLabel.__init__(self, *args, **kwargs)
        font = self.textItem.font()
        font.setPointSize(10)
        self.textItem.setFont(font)

        self.eventItem = None
    
    def mouseClickEvent(self, event):
        if event.button() == Qt.RightButton:
            if self.boundingRect().contains(event.pos()):
                if self.eventItem is not None:
                    if self.eventItem.raiseContextMenu(event):
                        event.accept()
