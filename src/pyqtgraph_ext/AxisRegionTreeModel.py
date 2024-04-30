""" Tree model for key-value pairs that uses PyQtKeyValueTreeItem for its data interface.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from pyqt_ext.tree import AbstractTreeModel
from pyqtgraph_ext import AxisRegionTreeItem
import qtawesome as qta


class AxisRegionTreeModel(AbstractTreeModel):
    
    def __init__(self, root: AxisRegionTreeItem = None, parent: QObject = None):
        AbstractTreeModel.__init__(self, root, parent)
        self.setColumnLabels(['X-Axis Regions'])
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            if self.supportedDropActions() != Qt.DropAction.IgnoreAction:
                # allow drops on the root item (i.e., this allows drops on the viewport away from other items)
                return Qt.ItemFlag.ItemIsDropEnabled
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
        if self.supportedDropActions() != Qt.DropAction.IgnoreAction:
            flags |= Qt.ItemFlag.ItemIsDragEnabled
            item: AxisRegionTreeItem = self.itemFromIndex(index)
            if item.is_group():
                flags |= Qt.ItemFlag.ItemIsDropEnabled
        return flags

    def data(self, index: QModelIndex, role: int):
        if not index.isValid():
            return
        item: AxisRegionTreeItem = self.itemFromIndex(index)
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            return item.get_data(index.column())
        elif role == Qt.ItemDataRole.DecorationRole:
            if index.column() == 0:
                if item.is_group():
                    return qta.icon('ph.folder-thin')

    def setData(self, index: QModelIndex, value, role: int) -> bool:
        item: AxisRegionTreeItem = self.itemFromIndex(index)
        if role == Qt.ItemDataRole.EditRole:
            success: bool = item.set_data(index.column(), value)
            if success:
                self.dataChanged.emit(index, index)
            return success
        return False


class AxisRegionDndTreeModel(AxisRegionTreeModel):

    def __init__(self, root: AxisRegionTreeItem = None, parent: QObject = None):
        AxisRegionTreeModel.__init__(self, root, parent)
    
    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.DropAction.MoveAction | Qt.DropAction.CopyAction