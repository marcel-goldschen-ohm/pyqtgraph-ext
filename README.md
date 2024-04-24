# pyqtgraph-ext
Collection of [PyQtGraph](https://www.pyqtgraph.org) widgets/tools with custom styling or behavior.

- [Install](#install)
- [AxisRegion](#axisregion)
- [View](#view)
- [Plot](#plot)
- [Figure](#figure)
- [PlotGrid](#plotgrid)
- [Graph](#graph)

# Install
Should work with PySide6, PyQt6, or PyQt5.
```shell
pip install PySide6 pyqtgraph-ext
```

# AxisRegion
`pyqtgraph.LinearRegionItem` with text label.

# View
`pyqtgraph.ViewBox` that knows how to draw `AxisRegion`s.

# Plot
`pyqtgraph.PlotItem` with MATLAB styling.

# Figure
`pyqtgraph.PlotWidget` with MATLAB styling.

# PlotGrid
`pyqtgraph.GraphicsLayoutWidget` that can set the size of all `View`s to be the same.

# Graph
`pyqtgraph.PlotDataItem` with context menu and style dialog.
