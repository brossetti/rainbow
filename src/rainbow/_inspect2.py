import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout
)


class InspectionWidget2(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        # add mouse move callback to viewer
        self.viewer.mouse_move_callbacks.append(self._mouse_moved)

        # initialize canvas
        self._canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self._axes = self._canvas.figure.subplots()
        self.toolbar = NavigationToolbar(self._canvas, self)

        # create layout
        layout_main = QVBoxLayout()
        layout_main.addWidget(self._canvas)
        layout_main.addWidget(self.toolbar)
        self.setLayout(layout_main)


    def _mouse_moved(self, viewer, event):
        self._axes.cla()
        for layer in viewer.layers.selection:
            coordinates = layer.world_to_data(self.viewer.cursor.position)
            xy_coordinates = [int(x) for x in coordinates[-2:]]
            if all(xy_coordinates >= layer.corner_pixels[0,-2:]) and all(xy_coordinates < layer.corner_pixels[1,-2:]):
                spectrum = layer.data[:,xy_coordinates[0], xy_coordinates[1]]
                self._axes.plot(spectrum)
                self._axes.figure.canvas.draw()


if __name__ == "__main__":
    import napari
    viewer = napari.Viewer()
    im1 = napari.utils.io.magic_imread('/Users/brossetti/Desktop/Lepto_10fluors_s001.tif')
    im2 = im1.copy() - 10
    viewer.add_image(im1)
    viewer.add_image(im2)
    napari.run()