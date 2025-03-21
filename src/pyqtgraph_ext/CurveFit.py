""" Curve fitting UI
"""

from __future__ import annotations
import numpy as np
import scipy as sp
import lmfit
from qtpy.QtCore import *
from qtpy.QtGui import *
from qtpy.QtWidgets import *
import pyqtgraph as pg
from pyqtgraph_ext import Figure, Graph


class CurveFitControlPanel(QScrollArea):

    fitRequested = Signal()
    fitChanged = Signal()

    def __init__(self, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)

        self.fit_result = {}

        self._fitTypeComboBox = QComboBox()
        self._fitTypeComboBox.addItems(['Line', 'Polynomial', 'Spline', 'Equation'])
        self._fitTypeComboBox.setCurrentText('Equation')
        self._fitTypeComboBox.currentIndexChanged.connect(self._onFitTypeChanged)

        # polynomial
        self._polynomialDegreeSpinBox = QSpinBox()
        self._polynomialDegreeSpinBox.setMinimum(0)
        self._polynomialDegreeSpinBox.setMaximum(100)
        self._polynomialDegreeSpinBox.setValue(2)
        self._polynomialDegreeSpinBox.valueChanged.connect(lambda value: self.fitChanged.emit())

        self._polynomialGroupBox = QGroupBox()
        form = QFormLayout(self._polynomialGroupBox)
        form.setContentsMargins(3, 3, 3, 3)
        form.setSpacing(3)
        form.setHorizontalSpacing(5)
        form.addRow('Degree', self._polynomialDegreeSpinBox)

        # spline
        self._splineDegreeSpinBox = QSpinBox()
        self._splineDegreeSpinBox.setMinimum(1)
        self._splineDegreeSpinBox.setMaximum(10000000)
        self._splineDegreeSpinBox.setValue(3)
        self._splineDegreeSpinBox.setSingleStep(2)
        self._splineDegreeSpinBox.valueChanged.connect(lambda value: self.fitChanged.emit())
        self._splineDegreeSpinBox.setToolTip('Degree of the spline polynomial\n3 for cubic spline recommended')
        splineDegreeLabel = QLabel('Degree')
        splineDegreeLabel.setToolTip(self._splineDegreeSpinBox.toolTip())

        self._splineSmoothingSpinBox = QDoubleSpinBox()
        self._splineSmoothingSpinBox.setSpecialValueText('Auto')
        self._splineSmoothingSpinBox.setMinimum(0)
        self._splineSmoothingSpinBox.setMaximum(10000000)
        self._splineSmoothingSpinBox.setValue(0)
        self._splineSmoothingSpinBox.valueChanged.connect(lambda value: self.fitChanged.emit())
        self._splineSmoothingSpinBox.setToolTip('Smoothing factor\nhigher for more smoothing\n0 -> auto ~ # data points')
        splineSmoothingLabel = QLabel('Smoothing')
        splineSmoothingLabel.setToolTip(self._splineSmoothingSpinBox.toolTip())

        self._splineNumberOfKnotsSpinBox = QSpinBox()
        self._splineNumberOfKnotsSpinBox.setSpecialValueText('Auto')
        self._splineNumberOfKnotsSpinBox.setMinimum(0)
        self._splineNumberOfKnotsSpinBox.setMaximum(10000000)
        self._splineNumberOfKnotsSpinBox.setValue(0)
        self._splineNumberOfKnotsSpinBox.valueChanged.connect(lambda value: self.fitChanged.emit())
        self._splineNumberOfKnotsSpinBox.setToolTip('Number of knots in the spline\nhigher for more flexibility\n0 -> auto')
        splineNumberOfKnotsLabel = QLabel('# Knots')
        splineNumberOfKnotsLabel.setToolTip(self._splineNumberOfKnotsSpinBox.toolTip())

        self._splineGroupBox = QGroupBox()
        form = QFormLayout(self._splineGroupBox)
        form.setContentsMargins(3, 3, 3, 3)
        form.setSpacing(3)
        form.setHorizontalSpacing(5)
        form.addRow(splineDegreeLabel, self._splineDegreeSpinBox)
        form.addRow(splineSmoothingLabel, self._splineSmoothingSpinBox)
        form.addRow(splineNumberOfKnotsLabel, self._splineNumberOfKnotsSpinBox)

        # equation
        self._equationEdit = QLineEdit()
        self._equationEdit.setPlaceholderText('a * x + b')
        self._equationEdit.editingFinished.connect(self._onEquationChanged)

        self._equationParamsTable = QTableWidget(0, 5)
        self._equationParamsTable.setHorizontalHeaderLabels(['Param', 'Value', 'Vary', 'Min', 'Max'])
        self._equationParamsTable.verticalHeader().setVisible(False)
        self._equationParamsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._equationParamsTable.model().dataChanged.connect(lambda model_index: self.fitChanged.emit())

        self._equationModel: lmfit.models.ExpressionModel | None = None

        self._equationGroupBox = QGroupBox()
        vbox = QVBoxLayout(self._equationGroupBox)
        vbox.setContentsMargins(3, 3, 3, 3)
        vbox.setSpacing(3)
        vbox.addWidget(self._equationEdit)
        vbox.addWidget(self._equationParamsTable)

        # custom equations
        self._customEquations = {}

        # controls
        self._fitButton = QPushButton('Fit')
        self._fitButton.pressed.connect(lambda: self.fitRequested.emit())

        # layout
        vbox = QVBoxLayout()
        vbox.setContentsMargins(5, 5, 5, 5)
        vbox.setSpacing(5)
        vbox.addWidget(self._fitTypeComboBox)
        vbox.addWidget(self._polynomialGroupBox)
        vbox.addWidget(self._splineGroupBox)
        vbox.addWidget(self._equationGroupBox)
        vbox.addWidget(self._fitButton)
        self._spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
        vbox.addSpacerItem(self._spacer)

        self.setFrameShape(QFrame.NoFrame)
        self.setLayout(vbox)
        self.setWidgetResizable(True)

    def fit(self, x, y):
        mask = np.isnan(x) | np.isnan(y)
        if np.any(mask):
            x = x[~mask]
            y = y[~mask]
        fitType = self._fitTypeComboBox.currentText()
        isCustomEquation = fitType in list(self._customEquations.keys())
        isEquation = (fitType == 'Equation') or isCustomEquation
        if fitType == 'Line':
            self.fit_result = {fitType: np.polyfit(x, y, 1)}
        elif fitType == 'Polynomial':
            degree = self._polynomialDegreeSpinBox.value()
            fit_result = {fitType: np.polyfit(x, y, degree)}
        elif fitType == 'Spline':
            n_pts = len(x)
            k = self._splineDegreeSpinBox.value()
            s = self._splineSmoothingSpinBox.value()
            if s == 0:
                s = n_pts
            n_knots = self._splineNumberOfKnotsSpinBox.value()
            if n_knots == 0:
                n_knots = None
            else:
                # ensure valid number of knots
                n_knots = min(max(2 * k + 2, n_knots), n_pts + k + 1)
            bspline: sp.interpolate.BSpline = sp.interpolate.make_splrep(x, y, s=s, nest=n_knots)
            fit_result = {fitType: bspline}
        elif isEquation and self._equationModel is not None:
            params = self.getEquationTableParams()
            for name, attrs in params.items():
                self._equationModel.set_param_hint(name, **attrs)
            _params = self._equationModel.make_params()
            result = self._equationModel.fit(y, params=_params, x=x)
            # print(result.fit_report())
            for name, value in result.params.valuesdict().items():
                params[name]['value'] = value
            self.setEquationTableParams(params)
            fit_result = {'Equation': params}
        self.fitChanged.emit()

    def predict(self, x, params = None):
        fitType = self._fitTypeComboBox.currentText()
        isCustomEquation = fitType in list(self._customEquations.keys())
        isEquation = (fitType == 'Equation') or isCustomEquation
        if params is None:
            if isEquation:
                params = self.getEquationTableParams()
            else:
                params = self.fit_result.get(fitType, None)
            if params is None:
                return
        if fitType == 'Mean':
            return np.full(len(x), params)
        elif fitType == 'Median':
            return np.full(len(x), params)
        elif fitType == 'Min':
            return np.full(len(x), params)
        elif fitType == 'Max':
            return np.full(len(x), params)
        elif fitType == 'Line':
            return np.polyval(params, x)
        elif fitType == 'Polynomial':
            return np.polyval(params, x)
        elif fitType == 'Spline':
            bspline: sp.interpolate.BSpline = params
            return bspline(x)
        elif isEquation and self._equationModel is not None:
            for name, attrs in params.items():
                self._equationModel.set_param_hint(name, **attrs)
            _params = self._equationModel.make_params()
            return self._equationModel.eval(params=_params, x=x)
    
    def previewEquation(self, x):
        params = self.getEquationTableParams()
        return self.predict(x, params)
    
    def isEquationSelected(self) -> bool:
        fitType = self._fitTypeComboBox.currentText()
        return (fitType == 'Equation') or (fitType in list(self._customEquations.keys()))
    
    # def fitGraph(self, data: pg.PlotDataItem, fit: pg.PlotDataItem, preview=False):
    #     x, y = data.getData()
    #     if x is None or y is None:
    #         return
    #     params = self.fit(x, y, preview=preview)
    #     y = self.predict(x, params)
    #     if y is None:
    #         y = np.full(len(x), np.nan)
    #     fit.setData(x, y)
    
    def setEquation(self, equation: str):
        # print('setEquation', equation)
        self._equationEdit.setText(equation)
        self._onEquationChanged()
    
    def addNamedEquation(self, name: str, equation: str, params: dict = None):
        for key in self._customEquations.keys():
            self._fitTypeComboBox.removeItem(self._fitTypeComboBox.findText(key))
        if len(self._customEquations) == 0:
            self._fitTypeComboBox.insertSeparator(self._fitTypeComboBox.count())
        self._customEquations[name] = {'equation': equation}
        if params is not None:
            self._customEquations[name]['params'] = params
        self._fitTypeComboBox.addItems(list(self._customEquations.keys()))
    
    def showEvent(self, event: QShowEvent) -> None:
        # this ensures _onFitTypeChanged is called after the widget is shown
        # otherwise the spacer doesn't resize properly on first show
        super().showEvent(event)
        self._onFitTypeChanged()
    
    def _onFitTypeChanged(self) -> None:
        # print('_onFitTypeChanged')
        fitType = self._fitTypeComboBox.currentText()
        isCustomEquation = fitType in list(self._customEquations.keys())
        isEquation = (fitType == 'Equation') or isCustomEquation
        self._polynomialGroupBox.setVisible(fitType == 'Polynomial')
        self._splineGroupBox.setVisible(fitType == 'Spline')
        self._equationGroupBox.setVisible(isEquation)
        self._fitButton.setVisible(isEquation)
        if isEquation:
            if isCustomEquation:
                equation = self._customEquations[fitType]['equation']
                self.blockSignals(True)  # prevent _onEquationChanged from emitting fitChanged
                self.setEquation(equation)
                self.blockSignals(False)
                customParams = self._customEquations[fitType].get('params', {})
                if customParams:
                    params = self.getEquationTableParams()
                    for name, attrs in customParams.items():
                        params[name] = {
                            'value': attrs.get('value', 0),
                            'vary': attrs.get('vary', True),
                            'min': attrs.get('min', -np.inf),
                            'max': attrs.get('max', np.inf)
                        }
                    self.setEquationTableParams(params)
            self._spacer.changeSize(0, 0, QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
        else:
            self._spacer.changeSize(0, 0, QSizePolicy.Policy.Ignored, QSizePolicy.Policy.MinimumExpanding)
        self.fitChanged.emit()
    
    def _onEquationChanged(self) -> None:
        # print('_onEquationChanged')
        equation = self._equationEdit.text().strip()     
        if equation == '':
            self._equationModel = None
            self.setEquationTableParams({})
        else:
            self._equationModel = lmfit.models.ExpressionModel(equation, independent_vars=['x'])
            params = self.getEquationTableParams()
            for name in self._equationModel.param_names:
                if name not in params:
                    params[name] = {
                        'value': 0,
                        'vary': True,
                        'min': -np.inf,
                        'max': np.inf
                    }
            params = {name: param for name, param in params.items() if name in self._equationModel.param_names}
            self.setEquationTableParams(params)
        self.fitChanged.emit()
    
    def getEquationTableParams(self) -> dict:
        params = {}
        for row in range(self._equationParamsTable.rowCount()):
            name = self._equationParamsTable.item(row, 0).text()
            try:
                value = float(self._equationParamsTable.item(row, 1).text())
            except:
                value = 0
            vary = self._equationParamsTable.item(row, 2).checkState() == Qt.CheckState.Checked
            try:
                value_min = float(self._equationParamsTable.item(row, 3).text())
            except:
                value_min = -np.inf
            try:
                value_max = float(self._equationParamsTable.item(row, 4).text())
            except:
                value_max = np.inf
            params[name] = {
                'value': value,
                'vary': vary,
                'min': value_min,
                'max': value_max
            }
        return params
    
    def setEquationTableParams(self, params) -> None:
        self._equationParamsTable.model().dataChanged.disconnect()  # needed because blockSignals not working!?
        self._equationParamsTable.blockSignals(True)  # not working!?
        self._equationParamsTable.clearContents()
        
        self._equationParamsTable.setRowCount(len(params))
        row = 0
        for name, attrs in params.items():
            value = attrs.get('value', 0)
            vary = attrs.get('vary', True)
            value_min = attrs.get('min', -np.inf)
            value_max = attrs.get('max', np.inf)

            name_item = QTableWidgetItem(name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            value_item = QTableWidgetItem(f'{value:.6g}')
            vary_item = QTableWidgetItem()
            vary_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            vary_item.setCheckState(Qt.CheckState.Checked if vary else Qt.CheckState.Unchecked)
            min_item = QTableWidgetItem(str(value_min))
            max_item = QTableWidgetItem(str(value_max))

            for col, item in enumerate([name_item, value_item, vary_item, min_item, max_item]):
                self._equationParamsTable.setItem(row, col, item)
            row += 1
        
        self._equationParamsTable.resizeColumnsToContents()
        self._equationParamsTable.blockSignals(False)
        self._equationParamsTable.model().dataChanged.connect(lambda model_index: self.fitChanged.emit())  # needed because blockSignals not working!?
   

class CurveFitWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.x: np.ndarray = None
        self.y: np.ndarray = None
        self.xfit: np.ndarray = None
        self.yfit: np.ndarray = None
        self._fit_model = None

        self.plot = Figure()
        view = self.plot.getViewBox()
        self.data = Graph(pen=pg.mkPen(color=view.nextColor(), width=1))
        self.fit = Graph(pen=pg.mkPen(color=view.nextColor(), width=1))
        self.plot.addItem(self.data)
        self.plot.addItem(self.fit)
        self.plot.setLabel('bottom', 'x')
        self.plot.setLabel('left', 'y')

        self.controlPanel = CurveFitControlPanel()
        self.controlPanel.fitRequested.connect(lambda: self._updateFit(preview=False))
        self.controlPanel.fitChanged.connect(lambda: self._updateFit(preview=True))

        hsplitter = QSplitter(Qt.Orientation.Horizontal)
        hsplitter.addWidget(self.controlPanel)
        hsplitter.addWidget(self.plot)
        hsplitter.setSizes([300, 700])

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(hsplitter)
    
    def setData(self, x: np.ndarray, y: np.ndarray, xfit: np.ndarray = None):
        if xfit is None:
            xfit = x
        self.x = x
        self.y = y
        self.xfit = xfit
        self.yfit = np.full(xfit.shape, np.nan)
        self.data.setData(x, y)
        self.fit.setData(xfit, yfit)
    
    def setFitRange(self, xfit: np.ndarray):
        self.xfit = xfit
        self.preview()
    
    def fit(self):
        self._fit_model = self.controlPanel.fit(self.x, self.y)
        self.yfit = self.controlPanel.predict(self.xfit, self._fit_model)
        self.fit.setData(self.xfit, self.yfit)
    
    def preview(self):
    


        if xfit is None:
            xfit = x
        self.data.setData(x, y)
        if self.controlPanel.isEquationSelected():
            yfit = self.controlPanel.previewEquation(xfit)
        else:
            params = self.controlPanel.fit(x, y)
            yfit = self.controlPanel.predict(xfit, params)
        self.fit.setData(xfit, yfit)
    
    def preview(self):
        x, y = self.data.getData()
        yfit = self.controlPanel.predict(xfit, params)
    
    def getFit(self) -> tuple[np.ndarray, np.ndarray]:
        return self.fit.getData()
    
    def _updateFit(self, preview=False):
        self.controlPanel.fitGraph(self.data, self.fit, preview=preview)
        x, y = self.data.getData()
        if x is None or y is None:
            return
        params = self.controlPanel.fit(x, y, preview=preview)
        y = self.predict(x, params)
        if y is None:
            y = np.full(len(x), np.nan)
        fit.setData(x, y)


def test_live():
    app = QApplication()

    # ui = CurveFitControlPanel()
    # ui.show()

    ui = CurveFitWidget()
    ui.show()

    ui.controlPanel.addNamedEquation(
        'Hill',
        'Ymax / (1 + (EC50 / x)**n)',
        {
            'Ymax': {'value': 1, 'vary': True, 'min': 0, 'max': np.inf},
            'EC50': {'value': 1, 'vary': True, 'min': 0, 'max': np.inf},
            'n': {'value': 1, 'vary': True, 'min': 0, 'max': np.inf}
        }
    )

    x = np.linspace(0, 10, 100)
    y = 3 * np.sin(2*np.pi*x*0.5) + np.random.randn(100)
    y[30:60] = np.nan
    ui.setData(x, y)

    app.exec()


if __name__ == '__main__':
    test_live()
