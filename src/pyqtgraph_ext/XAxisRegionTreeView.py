""" Tree view for a KeyValueTreeModel with context menu and mouse wheel expand/collapse.
"""

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
from pyqt_ext.utils import toColorStr
from pyqt_ext.widgets import ColorButton
from pyqt_ext.tree import TreeView
import pyqtgraph as pg
from pyqtgraph_ext import AxisRegion, XAxisRegion, XAxisRegionTreeItem, XAxisRegionTreeModel


class XAxisRegionTreeView(TreeView):

    def __init__(self, parent: QObject = None) -> None:
        TreeView.__init__(self, parent)

        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.selectionWasChanged.connect(self.updatePlots)

    def setModel(self, model: XAxisRegionTreeModel):
        TreeView.setModel(self, model)
        self.model().dataChanged.connect(self.onModelDataChanged)
    
    @Slot(QModelIndex, QModelIndex)
    def onModelDataChanged(self, topLeft: QModelIndex, bottomRight: QModelIndex):
        if getattr(self, '_allow_plot_updates', True):
            self.updatePlots()
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.modifiers() == Qt.KeyboardModifier.NoModifier:
                # if clicked without key modifier,
                # clear selection so click will process as new selection
                # This prevents deselecting a group's children and allows selecting a child in a group.
                self.selectionModel().clearSelection()
        QTreeView.mousePressEvent(self, event)
    
    @Slot(QItemSelection, QItemSelection)
    def selectionChanged(self, selected: QItemSelection, deselected: QItemSelection):
        QTreeView.selectionChanged(self, selected, deselected)
        
        if getattr(self, '_is_updating_selections', False):
            return
        self._is_updating_selections = True
        selection_items: list[XAxisRegionTreeItem] = self.selectedItems()
        
        # if group was selected, select all regions in group
        selected_items: list[XAxisRegionTreeItem] = [self.model().itemFromIndex(index) for index in selected.indexes()]
        for item in selected_items:
            if item.is_group():
                for child in item.children:
                    if child not in selection_items:
                        child_index = self.model().createIndex(child.sibling_index, 0, child)
                        self.selectionModel().select(child_index, QItemSelectionModel.SelectionFlag.Select)
                        selection_items.append(child)
        
        # if group was deselected, deselect all regions in group
        deselected_items: list[XAxisRegionTreeItem] = [self.model().itemFromIndex(index) for index in deselected.indexes()]
        for item in deselected_items:
            if item.is_group():
                for child in item.children:
                    if child not in selected_items:
                        if child in selection_items:
                            child_index = self.model().createIndex(child.sibling_index, 0, child)
                            self.selectionModel().select(child_index, QItemSelectionModel.SelectionFlag.Deselect)
                            selection_items.remove(child)
        
        self._is_updating_selections = False
        self.selectionWasChanged.emit()

    def contextMenu(self, index: QModelIndex = QModelIndex()) -> QMenu:
        menu: QMenu = TreeView.contextMenu(self, index)
       
        model: XAxisRegionTreeModel = self.model()
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
        
        item: XAxisRegionTreeItem = model.itemFromIndex(index)
        itemMenu = QMenu(item.name)
        if item.is_region():
            itemMenu.addAction('Edit', lambda item=item: self.editRegion(item))
            itemMenu.addSeparator()
        itemMenu.addAction('Delete', lambda item=item: self.deleteItem(item))
        menu.insertMenu(menu.actions()[0], itemMenu)
        menu.insertSeparator(menu.actions()[1])
        
        return menu
    
    def addRegion(self, region: dict, is_selected: bool = True):
        item = XAxisRegionTreeItem(region)
        self.model().appendItems([item], QModelIndex())
        if is_selected:
            self.selectionModel().select(self.model().indexFromItem(item), QItemSelectionModel.SelectionFlag.Select)
    
    def addGroup(self, name: str = 'New Group'):
        groupItem = XAxisRegionTreeItem({name: []})
        self.model().insertItems(0, [groupItem], QModelIndex())
    
    def editSelectedRegions(self):
        selectedRegions = self.selectedRegions()
        if not selectedRegions:
            return
        
        dlg = QDialog(self)
        dlg.setWindowTitle('Selected X axis regions')
        form = QFormLayout(dlg)
        form.setContentsMargins(5, 5, 5, 5)
        form.setSpacing(5)

        lb, ub = selectedRegions[0]['region']
        for i in range(1, len(selectedRegions)):
            lb_, ub_ = selectedRegions[i]['region']
            if lb_ != lb:
                lb = None
            if ub_ != ub:
                ub = None
        if lb is not None:
            minEdit = QLineEdit(f'{lb:.6f}')
        else:
            minEdit = QLineEdit('')
        if ub is not None:
            maxEdit = QLineEdit(f'{ub:.6f}')
        else:
            maxEdit = QLineEdit('')
        form.addRow('Min', minEdit)
        form.addRow('Max', maxEdit)

        movable = selectedRegions[0].get('movable', True)
        for i in range(1, len(selectedRegions)):
            if movable != selectedRegions[i].get('movable', True):
                movable = None
                break
        movableCheckBox = QCheckBox()
        if movable is not None:
            movableCheckBox.setChecked(movable)
        else:
            movableCheckBox.setTristate(True)
            movableCheckBox.setCheckState(Qt.CheckState.PartiallyChecked)
        form.addRow('Movable', movableCheckBox)

        color = selectedRegions[0].get('color', None)
        for i in range(1, len(selectedRegions)):
            if color != selectedRegions[i].get('color', None):
                color = None
                break
        colorButton = ColorButton(color)
        form.addRow('Color', colorButton)

        lineColor = selectedRegions[0].get('linecolor', None)
        for i in range(1, len(selectedRegions)):
            if lineColor != selectedRegions[i].get('linecolor', None):
                lineColor = None
                break
        lineColorButton = ColorButton(lineColor)
        form.addRow('Line Color', lineColorButton)

        lineWidth = selectedRegions[0].get('linewidth', 1)
        for i in range(1, len(selectedRegions)):
            if lineWidth != selectedRegions[i].get('linewidth', 1):
                lineWidth = -1
                break
        lineWidthSpinBox = QDoubleSpinBox()
        lineWidthSpinBox.setValue(lineWidth)
        form.addRow('Line Width', lineWidthSpinBox)

        text = selectedRegions[0].get('text', '')
        for i in range(1, len(selectedRegions)):
            if text != selectedRegions[i].get('text', ''):
                text = ''
                break
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
        
        lb = minEdit.text().strip()
        ub = maxEdit.text().strip()
        if lb != '':
            try:
                lb = float(lb)
            except Exception:
                QMessageBox.warning(self, 'Invalid range', 'Invalid range for region.', QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)
                return
            for region in selectedRegions:
                region['region'][0] = lb
        if ub != '':
            try:
                ub = float(ub)
            except Exception:
                QMessageBox.warning(self, 'Invalid range', 'Invalid range for region.', QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)
                return
            for region in selectedRegions:
                region['region'][1] = ub
        
        if movableCheckBox.checkState() != Qt.CheckState.PartiallyChecked:
            movable = movableCheckBox.isChecked()
            for region in selectedRegions:
                region['movable'] = movable
        
        color = colorButton.color()
        lineColor = lineColorButton.color()
        lineWidth = lineWidthSpinBox.value()
        text = textEdit.toPlainText().strip()
        
        for region in selectedRegions:
            if color is not None:
                region['color'] = toColorStr(color)
            if lineColor is not None:
                region['linecolor'] = toColorStr(lineColor)
            region['linewidth'] = lineWidth
            if text != '':
                region['text'] = text
        
        self.updateTreeView()
    
    def deleteSelectedItems(self):
        answer = QMessageBox.question(self, 'Delete selection?', 'Delete selection?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.storeState()
        selectedItems = self.selectedItems()
        self.model().beginResetModel()
        for item in selectedItems:
            modelItems = list(self.model().root().depth_first())
            if item in modelItems:
                item.parent.remove_child(item)
        self.model().endResetModel()
        self.restoreState()

        self.updatePlots()
    
    def editRegion(self, item: XAxisRegionTreeItem):
        if not item.is_region():
            return
        
        dlg = QDialog(self)
        dlg.setWindowTitle('X axis region')
        form = QFormLayout(dlg)
        form.setContentsMargins(5, 5, 5, 5)
        form.setSpacing(5)

        lb, ub = item._data['region']
        minEdit = QLineEdit(f'{lb:.6f}')
        maxEdit = QLineEdit(f'{ub:.6f}')
        form.addRow('Min', minEdit)
        form.addRow('Max', maxEdit)

        movableCheckBox = QCheckBox()
        movableCheckBox.setChecked(item._data.get('movable', True))
        form.addRow('Movable', movableCheckBox)

        colorButton = ColorButton(item._data.get('color', None))
        form.addRow('Color', colorButton)

        lineColorButton = ColorButton(item._data.get('linecolor', None))
        form.addRow('Line Color', lineColorButton)

        lineWidthSpinBox = QDoubleSpinBox()
        lineWidthSpinBox.setValue(item._data.get('linewidth', 1))
        form.addRow('Line Width', lineWidthSpinBox)

        text = item._data.get('text', '')
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
        
        try:
            lb = float(minEdit.text())
            ub = float(maxEdit.text())
        except Exception:
            QMessageBox.warning(self, 'Invalid range', 'Invalid range for region.', QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Ok)
            return
        
        item._data['region'] = [lb, ub]
        item._data['movable'] = movableCheckBox.isChecked()
        color = colorButton.color()
        if color is not None:
            item._data['color'] = toColorStr(color)
        lineColor = lineColorButton.color()
        if lineColor is not None:
            item._data['linecolor'] = toColorStr(lineColor)
        item._data['linewidth'] = lineWidthSpinBox.value()
        item._data['text'] = textEdit.toPlainText()
        
        self.updatePlots()
    
    def deleteItem(self, item: XAxisRegionTreeItem):
        self.askToRemoveItem(item)
        self.updatePlots()
    
    def selectedRegions(self) -> list[dict]:
        selectedItems = self.selectedItems()
        return [item._data for item in selectedItems if item.is_region()]
    
    def plots(self) -> list[pg.PlotItem]:
        return getattr(self, '_plots', [])
    
    def setPlots(self, plots: list[pg.PlotItem]):
        self._plots = plots
    
    def updatePlots(self):
        if not getattr(self, '_allow_plot_updates', True):
            return
        selectedRegions = self.selectedRegions()
        for plot in self.plots():
            xdim = getattr(plot, '_xdim', None)
            regionItems = [item for item in plot.vb.allChildren() if isinstance(item, XAxisRegion)]
            for regionItem in regionItems:
                # likely a bug in pyqtgraph, removing parent does not appropriately remove child items?
                plot.vb.removeItem(regionItem._textLabelItem)
                # now we can safely remove the parent region item
                plot.vb.removeItem(regionItem)
                regionItem.deleteLater()
            for region in selectedRegions:
                if (xdim is None) or (xdim == region.get('dim', None)):
                    regionItem = XAxisRegion()
                    regionItem.fromDict(region)
                    plot.vb.addItem(regionItem)
                    regionItem.toDict()  # updates region color, linecolor, etc.
                    regionItem.sigRegionChangeFinished.connect(lambda item, self=self, region=region: self.updateRegion(region))
    
    def updateRegion(self, region: dict):
        # update region's tree view item
        for item in self.model().root().depth_first():
            if item.is_region() and item._data is region:
                index: QModelIndex = self.model().createIndex(item.sibling_index, 0, item)
                self.model().dataChanged.emit(index, index)
                break
    
    def updateTreeView(self):
        self._allow_plot_updates = False
        # don't update plots for every dataChanged signal during resetModel
        self.resetModel()
        self._allow_plot_updates = True
        self.updatePlots()


def test_live():
    from pyqtgraph_ext import AxisRegionDndTreeModel, PlotGrid
    
    app = QApplication()

    data = [
        {
            'group A': [
                {'region': [8, 9], 'dim': 't', 'text': 'my label\n details...'},
            ],
        },
        {
            'group B': [
                {'region': [3, 4], 'dim': 'x'},
            ],
        },
        {'region': [35, 45], 'dim': 'x'},
    ]
    root = XAxisRegionTreeItem(data)
    model = AxisRegionDndTreeModel(root)
    view = XAxisRegionTreeView()
    view.setModel(model)
    view.show()
    view.resize(QSize(400, 400))

    grid = PlotGrid(2, 1)
    grid.setHasRegularLayout(True)
    for plot in grid.plots():
        plot._xdim = 'x'
    view.setPlots(grid.plots())
    grid.show()
    QTimer.singleShot(300, lambda: grid.applyRegularLayout())

    view.addRegion({'region': [15, 16], 'dim': 'x'})
    view.addRegion({'region': [25, 26], 'dim': 'x'})

    app.exec()

if __name__ == '__main__':
    test_live()
