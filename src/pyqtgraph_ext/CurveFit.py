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


# def fit_bspline(x: np.ndarray, y: np.ndarray, degree: int = 3, smoothing: float = 0, n_knots: int = 0) -> sp.interpolate.BSpline:
#     n_pts = len(x)
#     if smoothing == 0:
#         # default smoothing
#         smoothing = n_pts
#     if n_knots == 0:
#         # default number of knots
#         n_knots = None
#     if n_knots is not None:
#         # ensure valid number of knots
#         n_knots = min(max(2 * degree + 2, n_knots), n_pts + degree + 1)
#     bspline: sp.interpolate.BSpline = sp.interpolate.make_splrep(x, y, s=smoothing, nest=n_knots)
#     return bspline


# def fit_expression(expression: str | lmfit.models.ExpressionModel, x: np.ndarray, y: np.ndarray, independent_vars: list[str] = ['x'], params: dict = {}) -> lmfit.model.ModelResult:
#     model: lmfit.models.ExpressionModel = init_expression_model(expression=expression, independent_vars=independent_vars, params=params)
#     result: lmfit.model.ModelResult = model.fit(y, params=model.make_params(), x=x)
#     # print(result.fit_report())
#     # print(result.params.valuesdict())
#     return result


# def eval_expression(expression: str | lmfit.models.ExpressionModel, x: np.ndarray, independent_vars: list[str] = ['x'], params: dict = {}) -> np.ndarray:
#     model: lmfit.models.ExpressionModel = init_expression_model(expression=expression, independent_vars=independent_vars, params=params)
#     return model.eval(params=model.make_params(), x=x)


# def init_expression_model(expression: str | lmfit.models.ExpressionModel, independent_vars: list[str] = ['x'], params: dict = {}) -> lmfit.models.ExpressionModel:
#     if isinstance(expression, lmfit.models.ExpressionModel):
#         model = expression
#     else:
#         model = lmfit.models.ExpressionModel(expression, independent_vars=independent_vars)
#     for name in model.param_names:
#         if name in params:
#             model.set_param_hint(name, **params[name])
#         else:
#             # default param
#             model.set_param_hint(name, **{
#                 'value': 0,
#                 'vary': True,
#                 'min': -np.inf,
#                 'max': np.inf
#             })
#     return model


# def curve_fit(x: np.ndarray, y: np.ndarray, fit_type: str | np.ufunc, options: dict = {}):
#     mask = np.isnan(x) | np.isnan(y)
#     if np.any(mask):
#         x = x[~mask]
#         y = y[~mask]
#     if isinstance(fit_type, np.ufunc):
#         # e.g., np.mean, np.median, np.min, np.max
#         return fit_type(y)  # apply the ufunc to y
#     fit_type = fit_type.lower()
#     if fit_type == 'mean':
#         return np.mean(y)
#     elif fit_type == 'median':
#         return np.median(y)
#     elif fit_type == 'min':
#         return np.min(y)
#     elif fit_type == 'max':
#         return np.max(y)
#     elif fit_type == 'absmax':
#         return np.max(np.abs(y))
#     elif fit_type == 'line':
#         return np.polyfit(x, y, 1)
#     elif fit_type == 'polynomial':
#         degree = options['degree']
#         return np.polyfit(x, y, degree)
#     elif fit_type == 'bspline':
#         n_pts = len(x)
#         degree = options.get('degree', 3) # default to cubic spline
#         smoothing = options.get('smoothing', 0)
#         if smoothing == 0:
#             # default smoothing
#             smoothing = n_pts
#         n_knots = options.get('knots', 0)
#         if n_knots == 0:
#             # default number of knots
#             n_knots = None
#         else:
#             # ensure valid number of knots
#             n_knots = min(max(2 * degree + 2, n_knots), n_pts + degree + 1)
#         bspline: sp.interpolate.BSpline = sp.interpolate.make_splrep(x, y, s=smoothing, nest=n_knots)
#         return bspline
#     elif fit_type == 'equation':
#         equation: str = options['equation']
#         independent_vars: list[str] = options.get('independent_vars', ['x'])
#         params: dict[dict] = options.get('params', {})
#         model = lmfit.models.ExpressionModel(equation, independent_vars=independent_vars)
#         for name in model.param_names:
#             if name in params:
#                 model.set_param_hint(name, **params[name])
#             else:
#                 # default param
#                 model.set_param_hint(name, **{
#                     'value': 0,
#                     'vary': True,
#                     'min': -np.inf,
#                     'max': np.inf
#                 })
#         result = model.fit(y, params=model.make_params(), x=x)
#         # print(result.fit_report())
#         # print(result.params.valuesdict())
#         return result


# def curve_predict(self, x, fit_type: str, params):
#     fit_type = fit_type.lower()
#     if fit_type == 'mean':
#         return np.full(len(x), params)
#     elif fit_type == 'median':
#         return np.full(len(x), params)
#     elif fit_type == 'min':
#         return np.full(len(x), params)
#     elif fit_type == 'max':
#         return np.full(len(x), params)
#     elif fit_type == 'line':
#         return np.polyval(params, x)
#     elif fit_type == 'polynomial':
#         return np.polyval(params, x)
#     elif fit_type == 'bspline':
#         bspline: sp.interpolate.BSpline = params
#         return bspline(x)
#     elif fit_type == 'equation':
#         for name, attrs in params.items():
#             self._equationModel.set_param_hint(name, **attrs)
#         _params = self._equationModel.make_params()
#         return self._equationModel.eval(params=_params, x=x)


class CurveFitControlPanel(QScrollArea):

    paramsChanged = Signal()

    def __init__(self, *args, **kwargs):
        QScrollArea.__init__(self, *args, **kwargs)

        self._fit_result = None

        self._fitTypeComboBox = QComboBox()
        self._fitTypeComboBox.addItems(['Mean', 'Median', 'Min', 'Max'])
        self._fitTypeComboBox.insertSeparator(self._fitTypeComboBox.count())
        self._fitTypeComboBox.addItems(['Line', 'Polynomial', 'Spline'])  # BSpline too slow
        self._fitTypeComboBox.insertSeparator(self._fitTypeComboBox.count())
        self._fitTypeComboBox.addItems(['Expression'])
        self._fitTypeComboBox.setCurrentText('Expression')
        self._fitTypeComboBox.currentIndexChanged.connect(lambda index: self._onFitTypeChanged())

        # polynomial
        self._polynomialDegreeSpinBox = QSpinBox()
        self._polynomialDegreeSpinBox.setMinimum(0)
        self._polynomialDegreeSpinBox.setMaximum(100)
        self._polynomialDegreeSpinBox.setValue(2)
        self._polynomialDegreeSpinBox.valueChanged.connect(lambda value: self.paramsChanged.emit())

        self._polynomialGroupBox = QGroupBox()
        form = QFormLayout(self._polynomialGroupBox)
        form.setContentsMargins(3, 3, 3, 3)
        form.setSpacing(3)
        form.setHorizontalSpacing(5)
        form.addRow('Degree', self._polynomialDegreeSpinBox)

        # bspline
        self._bsplineDegreeSpinBox = QSpinBox()
        self._bsplineDegreeSpinBox.setMinimum(1)
        self._bsplineDegreeSpinBox.setMaximum(10000000)
        self._bsplineDegreeSpinBox.setValue(3)
        self._bsplineDegreeSpinBox.setSingleStep(2)
        self._bsplineDegreeSpinBox.valueChanged.connect(lambda value: self.paramsChanged.emit())
        self._bsplineDegreeSpinBox.setToolTip('Degree of the spline polynomial\n3 for cubic spline recommended')
        bsplineDegreeLabel = QLabel('Degree')
        bsplineDegreeLabel.setToolTip(self._bsplineDegreeSpinBox.toolTip())

        self._bsplineSmoothingSpinBox = QDoubleSpinBox()
        self._bsplineSmoothingSpinBox.setSpecialValueText('Auto')
        self._bsplineSmoothingSpinBox.setMinimum(0)
        self._bsplineSmoothingSpinBox.setMaximum(10000000)
        self._bsplineSmoothingSpinBox.setValue(0)
        self._bsplineSmoothingSpinBox.valueChanged.connect(lambda value: self.paramsChanged.emit())
        self._bsplineSmoothingSpinBox.setToolTip('Smoothing factor\nhigher for more smoothing\n0 -> auto ~ # data points')
        bsplineSmoothingLabel = QLabel('Smoothing')
        bsplineSmoothingLabel.setToolTip(self._bsplineSmoothingSpinBox.toolTip())

        self._bsplineNumberOfKnotsSpinBox = QSpinBox()
        self._bsplineNumberOfKnotsSpinBox.setSpecialValueText('Auto')
        self._bsplineNumberOfKnotsSpinBox.setMinimum(0)
        self._bsplineNumberOfKnotsSpinBox.setMaximum(10000000)
        self._bsplineNumberOfKnotsSpinBox.setValue(0)
        self._bsplineNumberOfKnotsSpinBox.valueChanged.connect(lambda value: self.paramsChanged.emit())
        self._bsplineNumberOfKnotsSpinBox.setToolTip('Number of knots in the spline\nhigher for more flexibility\n0 -> auto')
        bsplineNumberOfKnotsLabel = QLabel('# Knots')
        bsplineNumberOfKnotsLabel.setToolTip(self._bsplineNumberOfKnotsSpinBox.toolTip())

        self._bsplineGroupBox = QGroupBox()
        form = QFormLayout(self._bsplineGroupBox)
        form.setContentsMargins(3, 3, 3, 3)
        form.setSpacing(3)
        form.setHorizontalSpacing(5)
        form.addRow(bsplineDegreeLabel, self._bsplineDegreeSpinBox)
        form.addRow(bsplineSmoothingLabel, self._bsplineSmoothingSpinBox)
        form.addRow(bsplineNumberOfKnotsLabel, self._bsplineNumberOfKnotsSpinBox)

        # spline segments
        self._splineNumberOfSegmentsSpinbox = QSpinBox()
        self._splineNumberOfSegmentsSpinbox.setValue(10)
        self._splineNumberOfSegmentsSpinbox.setMinimum(1)
        self._splineNumberOfSegmentsSpinbox.valueChanged.connect(lambda value: self.paramsChanged.emit())

        self._splineGroupBox = QGroupBox()
        form = QFormLayout(self._splineGroupBox)
        form.setContentsMargins(3, 3, 3, 3)
        form.setSpacing(3)
        form.setHorizontalSpacing(5)
        form.addRow('# Segments', self._splineNumberOfSegmentsSpinbox)

        # y = f(x)
        self._expressionEdit = QLineEdit()
        self._expressionEdit.setPlaceholderText('a * x + b')
        self._expressionEdit.editingFinished.connect(self._onExpressionChanged)

        self._expressionParamsTable = QTableWidget(0, 5)
        self._expressionParamsTable.setHorizontalHeaderLabels(['Param', 'Value', 'Vary', 'Min', 'Max'])
        self._expressionParamsTable.verticalHeader().setVisible(False)
        self._expressionParamsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self._expressionParamsTable.model().dataChanged.connect(lambda model_index: self.paramsChanged.emit())

        self._expressionGroupBox = QGroupBox()
        vbox = QVBoxLayout(self._expressionGroupBox)
        vbox.setContentsMargins(3, 3, 3, 3)
        vbox.setSpacing(3)
        vbox.addWidget(self._expressionEdit)
        vbox.addWidget(self._expressionParamsTable)

        self._customExpressions = {}

        # layout
        vbox = QVBoxLayout()
        vbox.setContentsMargins(5, 5, 5, 5)
        vbox.setSpacing(5)
        vbox.addWidget(self._fitTypeComboBox)
        vbox.addWidget(self._polynomialGroupBox)
        vbox.addWidget(self._bsplineGroupBox)
        vbox.addWidget(self._splineGroupBox)
        vbox.addWidget(self._expressionGroupBox)
        # vbox.addWidget(self._fitButton)
        self._spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
        vbox.addSpacerItem(self._spacer)

        self.setFrameShape(QFrame.NoFrame)
        self.setLayout(vbox)
        self.setWidgetResizable(True)

    def fit(self, x, y):
        # print('fit')
        mask = np.isnan(x) | np.isnan(y)
        if np.any(mask):
            x = x[~mask]
            y = y[~mask]
        fitType = self._fitTypeComboBox.currentText()
        if fitType == 'Mean':
            return np.mean(y)
        elif fitType == 'Median':
            return np.median(y)
        elif fitType == 'Min':
            return np.min(y)
        elif fitType == 'Max':
            return np.max(y)
        elif fitType == 'AbsMax':
            return np.max(np.abs(y))
        elif fitType == 'Line':
            return np.polyfit(x, y, 1)
        elif fitType == 'Polynomial':
            degree = self._polynomialDegreeSpinBox.value()
            return np.polyfit(x, y, degree)
        elif fitType == 'BSpline':
            # !!! this is SLOW for even slightly large arrays
            n_pts = len(x)
            degree = self._bsplineDegreeSpinBox.value()
            smoothing = self._bsplineSmoothingSpinBox.value()
            if smoothing == 0:
                smoothing = n_pts
            n_knots = self._bsplineNumberOfKnotsSpinBox.value()
            if n_knots == 0:
                n_knots = None
            else:
                # ensure valid number of knots
                n_knots = min(max(2 * degree + 2, n_knots), n_pts + degree + 1)
            bspline: sp.interpolate.BSpline = sp.interpolate.make_splrep(x, y, s=smoothing, nest=n_knots)
            return bspline
        elif fitType == 'Spline':
            n_segments = self._splineNumberOfSegmentsSpinbox.value()
            segment_length = max(1, int(len(x) / n_segments))
            knots = x[segment_length:-segment_length:segment_length]
            # knots = x[::segment_length]
            # if len(knots) < 2:
            #     knots = x[[1, -2]]
            knots, coef, degree = sp.interpolate.splrep(x, y, t=knots)
            return knots, coef, degree
        elif fitType == 'Expression':
            model: lmfit.models.ExpressionModel = self._getExpressionModel()
            if model is None:
                return None
            result: lmfit.model.ModelResult = model.fit(y, params=model.make_params(), x=x)
            # print(result.fit_report())
            return result
        
    def predict(self, x, fit_result) -> np.ndarray:
        # print('predict')
        fitType = self._fitTypeComboBox.currentText()
        if fitType in ['Mean', 'Median', 'Min', 'Max', 'AbsMax']:
            return np.full(len(x), fit_result)
        elif fitType in ['Line', 'Polynomial']:
            return np.polyval(fit_result, x)
        elif fitType == 'BSpline':
            bspline: sp.interpolate.BSpline = fit_result
            return bspline(x)
        elif fitType == 'Spline':
            return sp.interpolate.splev(x, fit_result, der=0)
        elif fitType == 'Expression':
            if fit_result is None:
                model = self._getExpressionModel()
                if model is None:
                    return None
                params = model.make_params()
            else:
                result: lmfit.model.ModelResult = fit_result
                model: lmfit.models.ExpressionModel = fit_result.model
                params = result.params
            return model.eval(params=params, x=x)
    
    def setExpression(self, expression: str):
        # print('setExpression', expression)
        self._expressionEdit.setText(expression)
        self._onExpressionChanged()
    
    def addNamedExpression(self, name: str, expression: str, params: dict = None):
        # print('addNamedExpression', expression)
        for key in self._customExpressions.keys():
            self._fitTypeComboBox.removeItem(self._fitTypeComboBox.findText(key))
        if len(self._customExpressions) == 0:
            self._fitTypeComboBox.insertSeparator(self._fitTypeComboBox.count())
        self._customExpressions[name] = {'expression': expression}
        if params is not None:
            self._customExpressions[name]['params'] = params
        self._fitTypeComboBox.addItems(list(self._customExpressions.keys()))
    
    def showEvent(self, event: QShowEvent) -> None:
        # this ensures _onFitTypeChanged is called after the widget is shown
        # otherwise the spacer doesn't resize properly on first show
        super().showEvent(event)
        self._onFitTypeChanged()
    
    def _onFitTypeChanged(self) -> None:
        # print('_onFitTypeChanged')
        fitType = self._fitTypeComboBox.currentText()
        customExpression = self._customExpressions.get(fitType, None)
        if customExpression is not None:
            fitType = 'Expression'
            self._fitTypeComboBox.setCurrentText(fitType)
            self.setExpression(customExpression['expression'])
            params = self.getEquationTableParams()
            if 'params' in customExpression:
                for name, attrs in customExpression['params'].items():
                    for key, value in attrs.items():
                        params[name][key] = value
                self.setEquationTableParams(params)
        self._polynomialGroupBox.setVisible(fitType == 'Polynomial')
        self._bsplineGroupBox.setVisible(fitType == 'BSpline')
        self._splineGroupBox.setVisible(fitType == 'Spline')
        self._expressionGroupBox.setVisible(fitType == 'Expression')
        if fitType == 'Expression':
            self._spacer.changeSize(0, 0, QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
            if customExpression is not None:
                self._onExpressionChanged()
                return
        else:
            self._spacer.changeSize(0, 0, QSizePolicy.Policy.Ignored, QSizePolicy.Policy.MinimumExpanding)
        self.paramsChanged.emit()
    
    def _onExpressionChanged(self) -> None:
        # print('_onExpressionChanged')
        expression = self._expressionEdit.text().strip()     
        if expression == '':
            self.setEquationTableParams({})
        else:
            model = lmfit.models.ExpressionModel(expression, independent_vars=['x'])
            old_params = self.getEquationTableParams()
            new_params = {}
            for name in model.param_names:
                if name in old_params:
                    new_params[name] = old_params[name]
                else:
                    new_params[name] = {
                        'value': 0,
                        'vary': True,
                        'min': -np.inf,
                        'max': np.inf
                    }
            self.setEquationTableParams(new_params)
        self.paramsChanged.emit()
    
    def _getExpressionModel(self) -> lmfit.models.ExpressionModel | None:
        # print('_getExpressionModel')
        expression = self._expressionEdit.text().strip()
        if 'x' not in expression:
            return None
        model = lmfit.models.ExpressionModel(expression, independent_vars=['x'])
        params = self.getEquationTableParams()
        for name in model.param_names:
            model.set_param_hint(name, **params[name])
            # if name in params:
            #     model.set_param_hint(name, **params[name])
            # else:
            #     model.set_param_hint(name, **{
            #         'value': 0,
            #         'vary': True,
            #         'min': -np.inf,
            #         'max': np.inf
            #     })
        return model
    
    def getEquationTableParams(self) -> dict:
        # print('getEquationTableParams')
        params = {}
        for row in range(self._expressionParamsTable.rowCount()):
            name = self._expressionParamsTable.item(row, 0).text()
            try:
                value = float(self._expressionParamsTable.item(row, 1).text())
            except:
                value = 0
            vary = self._expressionParamsTable.item(row, 2).checkState() == Qt.CheckState.Checked
            try:
                value_min = float(self._expressionParamsTable.item(row, 3).text())
            except:
                value_min = -np.inf
            try:
                value_max = float(self._expressionParamsTable.item(row, 4).text())
            except:
                value_max = np.inf
            params[name] = {
                'value': value,
                'vary': vary,
                'min': value_min,
                'max': value_max
            }
        return params
    
    def setEquationTableParams(self, params: dict | lmfit.Parameters) -> None:
        # print('setEquationTableParams')
        if isinstance(params, lmfit.Parameters):
            params = params.valuesdict()

        self._expressionParamsTable.model().dataChanged.disconnect()  # needed because blockSignals not working!?
        self._expressionParamsTable.blockSignals(True)  # not working!?
        self._expressionParamsTable.clearContents()
        
        self._expressionParamsTable.setRowCount(len(params))
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
                self._expressionParamsTable.setItem(row, col, item)
            row += 1
        
        self._expressionParamsTable.resizeColumnsToContents()
        self._expressionParamsTable.blockSignals(False)
        self._expressionParamsTable.model().dataChanged.connect(lambda model_index: self.paramsChanged.emit())  # needed because blockSignals not working!?
   

class CurveFitWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plot = Figure()
        view = self.plot.getViewBox()
        self.data = Graph(pen=pg.mkPen(color=view.nextColor(), width=1))
        self.fit = Graph(pen=pg.mkPen(color=view.nextColor(), width=1))
        self.plot.addItem(self.data)
        self.plot.addItem(self.fit)
        self.plot.setLabel('bottom', 'x')
        self.plot.setLabel('left', 'y')

        self.controlPanel = CurveFitControlPanel()
        self.controlPanel.paramsChanged.connect(lambda: self._onFitChanged())

        hsplitter = QSplitter(Qt.Orientation.Horizontal)
        hsplitter.addWidget(self.controlPanel)
        hsplitter.addWidget(self.plot)
        hsplitter.setSizes([300, 700])

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)
        vbox.addWidget(hsplitter)
    
    def setData(self, x: np.ndarray, y: np.ndarray):
        yfit = np.full(x.shape, np.nan)
        self.data.setData(x, y)
        self.fit.setData(x, yfit)
        self._onFitChanged()
    
    def _onFitChanged(self, preview=False):
        x, y = self.data.getData()
        if x is None:
            return
        if preview and self.controlPanel._fitTypeComboBox.currentText() == 'Expression':
            result = None
        else:
            result = self.controlPanel.fit(x, y)
        y = self.controlPanel.predict(x, result)
        if y is None:
            y = np.full(len(x), np.nan)
        self.fit.setData(x, y)


def test_live():
    app = QApplication()

    ui = CurveFitWidget()
    controls = ui.controlPanel #CurveFitControlPanel()

    controls.addNamedExpression(
        'Hill Equation',
        'Y0 + Y1 / (1 + (EC50 / x)**n)',
        {
            'Y0': {'value': 0, 'vary': False, 'min': -np.inf, 'max': np.inf},
            'Y1': {'value': 1, 'vary': True, 'min': -np.inf, 'max': np.inf},
            'EC50': {'value': 1, 'vary': True, 'min': 0, 'max': np.inf},
            'n': {'value': 1, 'vary': True, 'min': 0, 'max': np.inf}
        }
    )

    ui.show()

    x = np.linspace(0, 10, 100)
    y = 3 * np.sin(2*np.pi*x*0.5) + np.random.randn(100)
    y[30:60] = np.nan
    ui.setData(x, y)

    app.exec()


if __name__ == '__main__':
    test_live()
    # result = fit_expression(
    #     np.array([1, 2, 3, 4, 5]),
    #     np.array([2.3, 2.8, 3.6, 4.5, 5.1]),
    #     expression='Ymax / (1 + (EC50 / x)**n)',
    #     independent_vars=['x'],
    #     params={
    #         'Ymax': {'value': 5, 'vary': True, 'min': 0, 'max': np.inf},
    #         'EC50': {'value': 2, 'vary': True, 'min': 0, 'max': np.inf},
    #         'n': {'value': 1, 'vary': True, 'min': 0, 'max': np.inf}
    #     }
    # )
    # print(result)
    # print(result)
    # # print(result.fit_report())
    # # print(result.params.valuesdict())
