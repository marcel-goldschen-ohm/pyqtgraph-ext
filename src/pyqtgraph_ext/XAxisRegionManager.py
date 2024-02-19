

from __future__ import annotations
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
from pyqtgraph_ext import XAxisRegion

class XAxisRegionManager(QListWidget):

    def __init__(self, *args, **kwargs):
        QListWidget.__init__(self, *args, **kwargs)
        
        self.regions: list[dict] = []
        self.plots: list[pg.PlotItem] = []
        self.xdim: str = None

        self.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.itemSelectionChanged.connect(self._on_selected_region_labels_changed)


class XAxisRegionManager2(QWidget):

    def __init__(self, *args, **kwargs):
        QWidget.__init__(self, *args, **kwargs)
        
        self.regions: list[dict] = []
        self.plots: list[pg.PlotItem] = []
        self.xdim: str = None

        self._region_label_list = QListWidget()
        self._region_label_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._region_label_list.itemSelectionChanged.connect(self._on_selected_region_labels_changed)

        self._edit_button = QPushButton('Edit')
        self._edit_button.setToolTip('Edit selected regions')
        # self._edit_button.pressed.connect(self._edit_selected_regions)

        self._delete_button = QPushButton('Delete')
        self._delete_button.setToolTip('Delete selected regions')
        self._delete_button.clicked.connect(self._delete_selected_regions)

        self._lock_button = QPushButton('Lock')
        self._lock_button.setToolTip('Lock selected regions')
        self._lock_button.clicked.connect(lambda: self._update_selected_regions(movable=False))

        self._unlock_button = QPushButton('Unlock')
        self._unlock_button.setToolTip('Unlock selected regions')
        self._unlock_button.clicked.connect(lambda: self._update_selected_regions(movable=True))

        controls_for_selected_regions_group = QGroupBox('Selected')
        grid = QGridLayout(controls_for_selected_regions_group)
        grid.setContentsMargins(3, 3, 3, 3)
        grid.setSpacing(5)
        grid.addWidget(self._edit_button, 0, 0)
        grid.addWidget(self._delete_button, 1, 0)
        grid.addWidget(self._lock_button, 0, 1)
        grid.addWidget(self._unlock_button, 1, 1)

        regions_group = QGroupBox('X axis regions')
        vbox = QVBoxLayout(regions_group)
        vbox.setContentsMargins(3, 3, 3, 3)
        vbox.setSpacing(5)
        vbox.addWidget(self._region_label_list)
        vbox.addWidget(controls_for_selected_regions_group)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(5, 5, 5, 5)
        vbox.setSpacing(20)
        vbox.addWidget(regions_group)
        vbox.addStretch()
    
    def add_region(self, region: dict, dim: str = None):
        if dim is None:
            dim = self.xdim
            if dim is None:
                dim = list(region['region'].keys())[0]
        xlim = region['region'][dim]
        if 'label' not in region:
            xmin, xmax = xlim
            region['label'] = self._unique_region_label(f'{dim}: {xmin:.6f}-{xmax:.6f}')
        if region not in self.regions:
            self.regions.append(region)
        for plot in self.plots:
            item = XAxisRegion(xlim)
            item._data = region
            item._dim = dim
            self._update_region_from_data(item)
            item.sigRegionChanged.connect(self._on_region_changed)
        self._update_region_label_list()
        self._region_label_list.blockSignals(True)
        for i in range(self._region_label_list.count()):
            item = self._region_label_list.item(i)
            if item.text() == region['label']:
                item.setSelected(True)
        self._region_label_list.blockSignals(False)

    
    def clear_regions(self):
        """ remove all regions from all plots
        """
        for plot in self.plots:
            items = [item for item in plot.vb.allChildren() if isinstance(item, XAxisRegion)]
            for item in items:
                plot.vb.removeItem(item)
                item.deleteLater()
    
    def update_regions(self):
        """ update all regions in all plots
        """
        for plot in self.plots:
            items = [item for item in plot.vb.allChildren() if isinstance(item, XAxisRegion)]
            for item in items:
                self._update_region_from_data(item)
    
    def _update_region_from_ui(self, item: XAxisRegion):
        item._data['region'][item._dim] = list(item.getRegion())
        item._data['movable'] = item.isMovable()
        item._data['label'] = item.label()
        item._data['text'] = item.text()
        item._data['color'] = toColorStr(item.color())
        item._data['linecolor'] = toColorStr(item.lineColor())
    
    def _update_region_from_data(self, item: XAxisRegion):
        item.blockSignals(True)
        item.setRegion(item._data['region'][item._dim])
        item.setIsMovable(item._data.get('movable', True))
        item.setLabel(item._data.get('label', ''))
        item.setText(item._data.get('text', ''))
        if 'color' in item._data:
            item.setColor(toQColor(item._data['color']))
        if 'linecolor' in item._data:
            item.setLineColor(toQColor(item._data['linecolor']))
        item.blockSignals(False)
    
    def _on_region_changed(self, item: XAxisRegion):
        self._update_region_from_ui(item)
        # ensures region is updated in all plots
        self.update_regions()
    
    def _update_region_label_list(self) -> None:
        self._region_label_list.blockSignals(True)
        selected_labels = [item.text() for item in self._region_label_list.selectedItems()]
        self._region_label_list.clear()
        labels = list(set([region['label'] for region in self.regions]))
        self._region_label_list.addItems(labels)
        for i in range(self._region_label_list.count()):
            item = self._region_label_list.item(i)
            item.setSelected(item.text() in selected_labels)
        self._region_label_list.blockSignals(False)
    
    def _selected_region_labels(self) -> list[str]:
        return [item.text() for item in self._region_label_list.selectedItems()]
    
    def _set_selected_region_labels(self, labels: list[str]) -> None:
        self._region_label_list.blockSignals(True)
        for i in range(self._region_label_list.count()):
            item = self._region_label_list.item(i)
            item.setSelected(item.text() in labels)
        self._region_label_list.blockSignals(False)
        self._on_selected_region_labels_changed()
    
    # def _add_selected_region_labels(self, labels: list[str]) -> None:
    #     selected_labels = self._selected_region_labels()
    #     for label in labels:
    #         if label not in selected_labels:
    #             selected_labels.append(label)
    #     self._set_selected_region_labels(selected_labels)
    
    def _on_selected_region_labels_changed(self) -> None:
        selected_labels = self._selected_region_labels()
        selected_regions = [region for region in self.regions if region['label'] in selected_labels and self.xdim in region['region']]
        self.clear_regions()
        # add selected region items
        for region in selected_regions:
            self.add_region(region, self.xdim)
    
    def _delete_selected_regions(self) -> None:
        reply = QMessageBox.question(self, 'Delete regions', 'Delete selected regions?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        self.clear_regions()
        selected_labels = self._selected_region_labels()
        selected_regions = [region for region in self.regions if region['label'] in selected_labels and self.xdim in region['region']]
        self.regions = [region for region in self.regions if region not in selected_regions]
        self._set_selected_region_labels([])
        self._update_region_label_list()
    
    def _update_selected_regions(self, movable: bool = None) -> None:
        selected_labels = self._selected_region_labels()
        selected_regions = [region for region in self.regions if region['label'] in selected_labels and self.xdim in region['region']]
        for region in selected_regions:
            if movable is not None:
                region['movable'] = movable
        self._update_region_items()
    
    # def _edit_selected_regions(self, label: str = None) -> None:
    #     if label is None or label == '':
    #         label, ok = QInputDialog.getText(self, 'Label Regions', 'Label selected regions:')
    #         label = label.strip()
    #         if not ok or label == '':
    #             return
        
    #     for plot in self.plots():
    #         view: View = plot.getViewBox()
    #         items: list[XAxisRegion] = [item for item in view.allChildren() if isinstance(item, XAxisRegion)]
    #         for item in items:
    #             item.setLabel(label)
    #             item._data['label'] = item.label()
        
    #     self._update_region_label_list()
    #     selected_labels = [item.text() for item in self._region_label_list.selectedItems()]
    #     if label not in selected_labels:
    #         selected_labels.append(label)
    #         self.set_selected_region_labels(selected_labels)
    
    def _unique_region_label(self, label: str) -> str:
        labels = [region['label'] for region in self.regions]
        if label not in labels:
            return label
        n = 1
        while f'{label}_{n}' in labels:
            n += 1
        return f'{label}_{n}'


def test_live():
    app = QApplication()

    ui = XAxisRegionManager()
    ui.show()

    ui.add_region({'region': {'x': [0, 1]}})
    ui.add_region({'region': {'t': [8, 9]}})

    app.exec()


if __name__ == '__main__':
    test_live()