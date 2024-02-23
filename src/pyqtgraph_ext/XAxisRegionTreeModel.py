""" Tree model for key-value pairs that uses PyQtKeyValueTreeItem for its data interface.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from pyqt_ext import AbstractTreeModel
from pyqtgraph_ext import XAxisRegionTreeItem
import qtawesome as qta


class XAxisRegionTreeModel(AbstractTreeModel):
    
    def __init__(self, root: XAxisRegionTreeItem = None, parent: QObject = None):
        AbstractTreeModel.__init__(self, root, parent)
        self.setColumnLabels(['Axis Regions'])
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            if self.supportedDropActions() != Qt.DropAction.IgnoreAction:
                # allow drops on the root item (i.e., this allows drops on the viewport away from other items)
                return Qt.ItemFlag.ItemIsDropEnabled
            return Qt.ItemFlag.NoItemFlags
        item: XAxisRegionTreeItem = self.itemFromIndex(index)
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
        if self.supportedDropActions() != Qt.DropAction.IgnoreAction:
            flags |= Qt.ItemFlag.ItemIsDragEnabled
            if item.is_group():
                flags |= Qt.ItemFlag.ItemIsDropEnabled
        return flags

    def data(self, index: QModelIndex, role: int):
        if not index.isValid():
            return
        item: XAxisRegionTreeItem = self.itemFromIndex(index)
        if item is None:
            return
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return item.data(index.column())
        elif role == Qt.ItemDataRole.DecorationRole:
            if index.column() == 0:
                if item.is_group():
                    return qta.icon('ph.folder-thin')

    def setData(self, index: QModelIndex, value, role: int) -> bool:
        if role != Qt.ItemDataRole.EditRole:
            return False
        item: XAxisRegionTreeItem = self.itemFromIndex(index)
        if item is None:
            return False
        if role == Qt.ItemDataRole.EditRole:
            success: bool = item.set_data(index.column(), value)
            if success:
                self.dataChanged.emit(index, index)
            return success
        return False


class AxisRegionDndTreeModel(XAxisRegionTreeModel):

    def __init__(self, root: XAxisRegionTreeItem = None, parent: QObject = None):
        XAxisRegionTreeModel.__init__(self, root, parent)
    
    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.DropAction.MoveAction | Qt.DropAction.CopyAction