import numpy as np
# from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.backends.qt_compat import QtWidgets
from matplotlib.figure import Figure
from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

class InspectionWidget(QtWidgets.QMainWindow):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        # add mouse move callback to all visible layers
        for layer in self.viewer.layers:
            if layer._type_string == 'image' and layer.visible and layer.ndim > self.viewer.dims.ndisplay:
                if self._plot_spectra not in layer.mouse_move_callbacks:
                    layer.mouse_move_callbacks.append(self._plot_spectra)
        
        # display opening graph
        self._main = QtWidgets.QWidget()
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)
        dynamic_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        layout.addWidget(dynamic_canvas)
        layout.addWidget(NavigationToolbar(dynamic_canvas, self))
        self._dynamic_ax = dynamic_canvas.figure.subplots()
        # Set up a Line2D.
        (self._line,) = self._dynamic_ax.plot(layer.data[:,0,0])

    def _plot_spectra(self, layer, event):
        coordinates = layer.world_to_data(self.viewer.cursor.position)
        xy_coordinates = [int(x) for x in coordinates[-2:]]
        if all(xy_coordinates >= layer.corner_pixels[0,-2:]) and all(xy_coordinates < layer.corner_pixels[1,-2:]):
            print(xy_coordinates)
            self._line.set_data(np.linspace(0,22,23),layer.data[:,xy_coordinates[0], xy_coordinates[1]])
            self._line.figure.canvas.draw()

if __name__ == "__main__":
    import napari
    viewer = napari.Viewer()
    im = napari.utils.io.magic_imread('/Users/brossetti/Desktop/Lepto_10fluors_s001.tif')
    viewer.add_image(im)
    napari.run()