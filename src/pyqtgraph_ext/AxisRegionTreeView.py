""" Tree view for a KeyValueTreeModel with context menu and mouse wheel expand/collapse.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from pyqt_ext import AbstractTreeView
from pyqtgraph_ext import AxisRegionTreeItem, AxisRegionTreeModel


class AxisRegionTreeView(AbstractTreeView):

    def __init__(self, parent: QObject = None) -> None:
        AbstractTreeView.__init__(self, parent)

        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                # if clicked without key modifier,
                # clear selection so click will process as new selection
                self.selectionModel().clearSelection()
        QTreeView.mousePressEvent(self, event)
    
    @Slot(QItemSelection, QItemSelection)
    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        QTreeView.selectionChanged(self, selected, deselected)
        
        if getattr(self, '_is_updating_group_selections', False):
            return
        self._is_updating_group_selections = True
        # print('-----')
        selection_items: list[AxisRegionTreeItem] = [self.model().itemFromIndex(index) for index in self.selectionModel().selectedIndexes()]
        # print('selection_items', [repr(item) for item in selection_items])
        
        # if group was selected, select all regions in group
        selected_items: list[AxisRegionTreeItem] = [self.model().itemFromIndex(index) for index in selected.indexes()]
        # print('selected_items', [repr(item) for item in selected_items])
        for item in selected_items:
            if item.is_group():
                # print('selected', repr(item))
                for child in item.children:
                    if child not in selection_items:
                        child_index = self.model().createIndex(child.sibling_index, 0, child)
                        self.selectionModel().select(child_index, QItemSelectionModel.SelectionFlag.Select)
                        selection_items.append(child)
        
        # if group was deselected, deselect all regions in group
        deselected_items: list[AxisRegionTreeItem] = [self.model().itemFromIndex(index) for index in deselected.indexes()]
        # print('deselected_items', [repr(item) for item in deselected_items])
        for item in deselected_items:
            if item.is_group():
                # print('deselected', repr(item))
                for child in item.children:
                    if child not in selected_items:
                        if child in selection_items:
                            child_index = self.model().createIndex(child.sibling_index, 0, child)
                            self.selectionModel().select(child_index, QItemSelectionModel.SelectionFlag.Deselect)
                            selection_items.remove(child)
        
        # print('selection_items', [repr(item) for item in selection_items])
        # print('-----')
        self._is_updating_group_selections = False
        self.selectionWasChanged.emit()

    def contextMenu(self, index: QModelIndex = QModelIndex()) -> QMenu:
        menu: QMenu = AbstractTreeView.contextMenu(self, index)
       
        model: AxisRegionTreeModel = self.model()
        if model is None:
            return menu
        
        menu.addSeparator()
        menu.addAction('Add group', lambda: self.addGroup())
        menu.addSeparator()
        menu.addAction('Edit selected regions', self.editSelectedRegions)
        menu.addSeparator()
        menu.addAction('Delete selected regions/groups', self.deleteSelectedItems)
        
        if not index.isValid():
            return menu
        
        item: AxisRegionTreeItem = model.itemFromIndex(index)
        itemMenu = QMenu(repr(item))
        itemMenu.addAction('Edit', lambda item=item: self.editItem(item))
        itemMenu.addSeparator()
        itemMenu.addAction('Delete', lambda item=item: self.deleteItem(item))
        menu.insertMenu(menu.actions()[0], itemMenu)
        menu.insertSeparator(menu.actions()[1])
        
        return menu
    
    def addGroup(self, name: str = 'Group'):
        groupItem = AxisRegionTreeItem({name: []})
        self.model().insertItems(0, [groupItem], QModelIndex())
        print(self.model().root()._group_list)
    
    def editSelectedRegions(self):
        pass # TODO
    
    def deleteSelectedItems(self):
        answer = QMessageBox.question(self, 'Delete selection?', 'Delete selection?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.storeState()
            selectedItems = self.selectedItems()
            self.model().beginResetModel()
            for item in selectedItems:
                modelItems = list(self.model().root().depth_first())
                if item in modelItems:
                    item.parent.remove_child(item)
            self.model().endResetModel()
            self.restoreState()
    
    def editItem(self, item: AxisRegionTreeItem):
        pass # TODO
    
    def deleteItem(self, item: AxisRegionTreeItem):
        self.askToRemoveItem(item)


def test_live():
    from pyqtgraph_ext import AxisRegionDndTreeModel
    
    app = QApplication()

    data = [
        {
            'group A': [
                # {'region': {'x': [0, 1]}}, 
                {'region': {'t': [8, 9]}, 'text': 'my label\n details...'}
            ],
        },
        {
            'group B': [
                {'region': {'x': [3, 4]}}, 
                # {'region': {'t': [18, 19]}}
            ],
        },
        {'region': {'x': [35, 45]}}, 
        # {'region': {'t': [180, 190]}},
    ]
    root = AxisRegionTreeItem(data)
    model = AxisRegionDndTreeModel(root)
    view = AxisRegionTreeView()
    view.setModel(model)
    view.show()
    view.resize(QSize(400, 400))

    app.exec()

if __name__ == '__main__':
    test_live()
