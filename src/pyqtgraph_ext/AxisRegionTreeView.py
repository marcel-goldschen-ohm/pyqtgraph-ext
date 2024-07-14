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
from pyqtgraph_ext import AxisRegion, XAxisRegion, YAxisRegion, AxisRegionTreeItem, AxisRegionTreeModel


class AxisRegionTreeView(TreeView):

    sigRegionChangeFinished = Signal()

    def __init__(self, parent: QObject = None) -> None:
        TreeView.__init__(self, parent)

        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

        self.selectionWasChanged.connect(self.updatePlots)

    def setModel(self, model: AxisRegionTreeModel):
        TreeView.setModel(self, model)
        self.model().dataChanged.connect(self.onModelDataChanged)
        self.model().rowsRemoved.connect(self.onModelDataChanged)
    
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
        # print('\n\nSelected:')
        # for i, index in enumerate(selected.indexes()):
        #     print(i, self.model().itemFromIndex(index).get_data(0))

        # print('\n\nDeselected:')
        # for i, index in enumerate(deselected.indexes()):
        #     print(i, self.model().itemFromIndex(index).get_data(0))

        QTreeView.selectionChanged(self, selected, deselected)

        if getattr(self, '_is_updating_selections', False):
            return
        self._is_updating_selections = True
        
        # if group was selected, select all regions in group
        indexes = selected.indexes()
        for index in indexes:
            item = self.model().itemFromIndex(index)
            if item.is_group():
                for child in item.children:
                    child_index = self.model().createIndex(child.sibling_index, 0, child)
                    if not self.selectionModel().isSelected(child_index):
                        flags = (
                            QItemSelectionModel.SelectionFlag.Select |
                            QItemSelectionModel.SelectionFlag.Rows
                        )
                        self.selectionModel().select(child_index, flags)
        
        # if group was deselected, deselect all regions in group
        indexes = deselected.indexes()
        for index in indexes:
            item = self.model().itemFromIndex(index)
            if item.is_group():
                for child in item.children:
                    child_index = self.model().createIndex(child.sibling_index, 0, child)
                    if self.selectionModel().isSelected(child_index):
                        flags = (
                            QItemSelectionModel.SelectionFlag.Deselect |
                            QItemSelectionModel.SelectionFlag.Rows
                        )
                        self.selectionModel().select(child_index, flags)
        
        self._is_updating_selections = False
        
        # ensure plots are updated
        self.selectionWasChanged.emit()

    def contextMenu(self, index: QModelIndex = QModelIndex()) -> QMenu:
        menu: QMenu = TreeView.contextMenu(self, index)
       
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
        
        item: XarrayTreeItem = model.itemFromIndex(index)
        if item.is_region():
            item_action = menu.actions()[0]
            item_menu = menu.menuInAction(item_action)
            delete_action = item_menu.actions()[0]
            item_menu.addAction('Edit', lambda item=item: self.editRegion(item))
            item_menu.addSeparator()
            item_menu.addAction(delete_action)
        
        return menu
    
    def addRegion(self, region: dict, is_selected: bool = True):
        item = AxisRegionTreeItem(region)
        self.model().appendItems([item], QModelIndex())
        if is_selected:
            flags = (
                QItemSelectionModel.SelectionFlag.Select |
                QItemSelectionModel.SelectionFlag.Rows
            )
            self.selectionModel().select(self.model().indexFromItem(item), flags)
    
    def addGroup(self, name: str = 'New Group'):
        groupItem = AxisRegionTreeItem({name: []})
        self.model().insertItems(0, [groupItem], QModelIndex())
    
    def editSelectedRegions(self):
        selectedRegionItems = self.selectedRegionItems()
        if not selectedRegionItems:
            return
        selectedRegions = [item._data for item in selectedRegionItems]
        
        dlg = QDialog(self)
        dlg.setWindowTitle('Selected X axis regions')
        form = QFormLayout(dlg)
        form.setContentsMargins(5, 5, 5, 5)
        form.setSpacing(5)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        region_str = selectedRegionItems[0].region_str()
        for i in range(1, len(selectedRegionItems)):
            region_str_ = selectedRegionItems[i].region_str()
            if region_str_ != region_str:
                region_str = None
                break
        if region_str is not None:
            regionEdit = QLineEdit(region_str)
        else:
            regionEdit = QLineEdit('')
        form.addRow('Region', regionEdit)

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
        
        color = colorButton.color()
        lineColor = lineColorButton.color()
        lineWidth = lineWidthSpinBox.value()
        text = textEdit.toPlainText().strip()
        
        for regionItem in selectedRegionItems:
            if regionEdit.text() != '':
                regionItem.region = regionEdit.text()
            if movableCheckBox.checkState() != Qt.CheckState.PartiallyChecked:
                regionItem._data['movable'] = movableCheckBox.isChecked()
            if color is not None:
                regionItem._data['color'] = toColorStr(color)
            if lineColor is not None:
                regionItem._data['linecolor'] = toColorStr(lineColor)
            regionItem._data['linewidth'] = lineWidth
            if text != '':
                regionItem._data['text'] = text
        
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
    
    def editRegion(self, item: AxisRegionTreeItem):
        if not item.is_region():
            return
        
        dlg = QDialog(self)
        dlg.setWindowTitle('Axis regions')
        form = QFormLayout(dlg)
        form.setContentsMargins(5, 5, 5, 5)
        form.setSpacing(5)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        regionEdit = QLineEdit(item.region_str())
        form.addRow('Region', regionEdit)

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
        
        item.region = regionEdit.text()
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
    
    def deleteItem(self, item: AxisRegionTreeItem):
        self.askToRemoveItem(item)
        self.updatePlots()
    
    def selectedRegionItems(self) -> list[AxisRegionTreeItem]:
        return [item for item in self.selectedItems() if item.is_region()]
    
    def plots(self) -> list[pg.PlotItem]:
        return getattr(self, '_plots', [])
    
    def setPlots(self, plots: list[pg.PlotItem]):
        self._plots = plots
        self.updatePlots()
    
    def updatePlots(self):
        if getattr(self, '_is_updating_selections', False):
            return
        if not getattr(self, '_allow_plot_updates', True):
            return
        selectedRegions = [item._data for item in self.selectedRegionItems()]
        for plot in self.plots():
            xdim, ydim = getattr(plot, '_dims', ['x', 'y'])
            # clear current region items
            regionItems = [item for item in plot.vb.allChildren() if isinstance(item, AxisRegion)]
            for regionItem in regionItems:
                # likely a bug in pyqtgraph, removing parent does not appropriately remove child items?
                plot.vb.removeItem(regionItem._textLabelItem)
                # now we can safely remove the parent region item
                plot.vb.removeItem(regionItem)
                regionItem.deleteLater()
            # add selected region items
            for region in selectedRegions:
                regionItem = None
                isx = xdim in region['region']
                isy = ydim in region['region']
                if isx and isy:
                    pass # TODO: add support for 2D regions
                elif isx:
                    regionItem = XAxisRegion()
                    regionItem._dim = xdim
                elif isy:
                    regionItem = YAxisRegion()
                    regionItem._dim = ydim
                if regionItem is not None:
                    regionItem.fromDict(region, regionItem._dim)
                    regionItem._data = region
                    plot.vb.addItem(regionItem)
                    regionItem.sigRegionChangeFinished.connect(lambda item, self=self, region=region: self.updateRegion(region))
                    regionItem.sigRegionChangeFinished.connect(lambda item, self=self: self.sigRegionChangeFinished.emit())
    
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
                {'region': {'t': [8, 9]}, 'text': 'my label\n details...'}
            ],
        },
        {
            'group B': [
                {'region': {'x': [3.145234523445, 4.2345243432542245]}}, 
            ],
        },
        {'region': {'x': [35, 45]}}, 
        {'region': {'a': [-35, 45], 'b': [-3.23523453422345, 1], 'c': [-3, -1]}}, 
    ]
    root = AxisRegionTreeItem(data)
    model = AxisRegionDndTreeModel(root)
    view = AxisRegionTreeView()
    view.setModel(model)
    view.show()
    view.resize(QSize(400, 400))

    grid = PlotGrid(2, 1)
    grid.setHasRegularLayout(True)
    grid.plots()[1].setXLink(grid.plots()[0])
    # for plot in grid.plots():
    #     plot._dims = ['x', 'y']
    view.setPlots(grid.plots())
    grid.show()
    QTimer.singleShot(300, lambda: grid.applyRegularLayout())

    view.addRegion({'region': {'x': [15, 16]}})
    view.addRegion({'region': {'x': [25, 26]}})

    app.exec()

if __name__ == '__main__':
    test_live()
