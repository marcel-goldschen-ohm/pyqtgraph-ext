# pyqtgraph-ext
Collection of [PyQtGraph](https://www.pyqtgraph.org) widgets/tools with custom styling or behavior.

![GitHub Tag](https://img.shields.io/github/v/tag/marcel-goldschen-ohm/pyqtgraph-ext?cacheSeconds=1)
![build-test](https://github.com/marcel-goldschen-ohm/pyqtgraph-ext/actions/workflows/build-test.yml/badge.svg)
![GitHub Release](https://img.shields.io/github/v/release/marcel-goldschen-ohm/pyqtgraph-ext?include_prereleases&cacheSeconds=1)
![publish](https://github.com/marcel-goldschen-ohm/pyqtgraph-ext/actions/workflows/publish.yml/badge.svg)

The goal of this repo is to provide useful extensions to PyQtGraph all in one place. There are several other PyQtGraph extensions out there, but to my knowledge all of these are very limited in scope. Given this goal, **I encourage everyone to contribute your own extensions to this repo!**

In addition to being useful out-of-the-box, you may find these tools to be helpful templates for rolling your own custom widgets.

- [Install](#install)
- [Documentation](#documentation)

## Install
Requires a PyQt package. Should work with PySide6, PyQt6, or PyQt5.
```shell
pip install PySide6
```
Install latest release version:
```shell
pip install pyqtgraph-ext
```
Or install latest development version:
```shell
pip install pyqtgraph-ext@git+https://github.com/marcel-goldschen-ohm/pyqtgraph-ext
```

## Documentation
:construction:

- [AxisRegion](#axisregion)
- [View](#view)
- [Plot](#plot)
- [Figure](#figure)
- [PlotGrid](#plotgrid)
- [Graph](#graph)

### AxisRegion
`pyqtgraph.LinearRegionItem` with text label.

### View
`pyqtgraph.ViewBox` that knows how to draw `AxisRegion`s.

### Plot
`pyqtgraph.PlotItem` with MATLAB styling.

### Figure
`pyqtgraph.PlotWidget` with MATLAB styling.

### PlotGrid
`pyqtgraph.GraphicsLayoutWidget` that can set the size of all `View`s to be the same.

### Graph
`pyqtgraph.PlotDataItem` with context menu and style dialog.

## Dev Notes
```
pdm lock --dev
pdm lock --prod -L pdm.prod.lock
```