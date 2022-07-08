import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvas
# from matplotlib.backends.backend_qtagg import (
#     NavigationToolbar2QT as NavigationToolbar,
# )
# from matplotlib.backends.qt_compat import QtWidgets

# from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QDoubleSpinBox
)

# class InspectionWidget(QMainWindow):
class InspectionWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        # add mouse move callback to all selected layers
        for layer in self.viewer.layers:
            if layer._type_string == 'image' and layer.ndim > self.viewer.dims.ndisplay:
                if self._plot_spectra not in layer.mouse_move_callbacks:
                    layer.mouse_move_callbacks.append(self._plot_spectra)


        # initialize interface
        self.view = FigureCanvas(Figure(figsize=(5, 3)))
        self.axes = self.view.figure.subplots()
        # self.toolbar = NavigationToolbar2QT(self.view, self)
        self.mu_input = QDoubleSpinBox()
        self.std_input = QDoubleSpinBox()
        self.mu_input.setPrefix("μ: ")
        self.std_input.setPrefix("σ: ")
        self.std_input.setValue(10)

        #  Create layout
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.mu_input)
        input_layout.addWidget(self.std_input)
        vlayout = QVBoxLayout()
        # vlayout.addWidget(self.toolbar)
        vlayout.addWidget(self.view)
        vlayout.addLayout(input_layout)
        self.setLayout(vlayout)

        # connect inputs with on_change method
        # self.mu_input.valueChanged.connect(self.on_change)
        # self.std_input.valueChanged.connect(self.on_change)

        # self.on_change()

        
        # self._main = QWidget()
        # self.setCentralWidget(self._main)

        # layout = QVBoxLayout(self._main)
        # dynamic_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        # layout.addWidget(dynamic_canvas)
        # layout.addWidget(NavigationToolbar(dynamic_canvas, self))
        # self._dynamic_ax = dynamic_canvas.figure.subplots()
        # Set up a Line2D.
        # (self._line,) = self._dynamic_ax.plot(layer.data[:,0,0])

        # layout = QVBoxLayout(self._main)

        # # create canvas element for plotting
        # canvas = FigureCanvas(Figure(figsize=(5, 3)))
        # self._axes = canvas.figure.subplots()

        # # create settings elements
        self._normalization = 0
        # # label_normalization = QLabel('normalization:')
        # # setting_normalization = QComboBox()
        # # setting_normalization.addItems(['max', 'sum', 'raw'])
        # # setting_normalization.activated.connect(self.normalization_changed)

        # # add everything to the main vbox layout
        # layout.addWidget(canvas)
        # layout.addWidget(NavigationToolbar(canvas, self))
        # # layout.addWidget(label_normalization)
        # # layout.addWidget(setting_normalization)

        # # Set up a Line2D.        
        # (self._line,) = self._axes.plot(layer.data[:,0,0])

    
    def normalization_changed(self, ind):
        self._normalization = ind

    def _plot_spectra(self, layer, event):
        coordinates = layer.world_to_data(self.viewer.cursor.position)
        xy_coordinates = [int(x) for x in coordinates[-2:]]
        if all(xy_coordinates >= layer.corner_pixels[0,-2:]) and all(xy_coordinates < layer.corner_pixels[1,-2:]):
            spectrum = layer.data[:,xy_coordinates[0], xy_coordinates[1]]
            if self._normalization == 0:
                spectrum = np.divide(spectrum, np.max(spectrum))
            elif self._normalization == 1:
                spectrum = np.divide(spectrum, np.sum(spectrum))
            self._line.set_data(np.linspace(0,22,23),spectrum)
            self._line.figure.canvas.draw()

if __name__ == "__main__":
    import napari
    viewer = napari.Viewer()
    im = napari.utils.io.magic_imread('/Users/brossetti/Desktop/Lepto_10fluors_s001.tif')
    viewer.add_image(im)
    napari.run()