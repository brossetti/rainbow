import _utils

import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QHBoxLayout
)
from napari.layers import Image


class InspectionWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        # add mouse move callback to viewer
        self.viewer.mouse_move_callbacks.append(self._mouse_moved)

        # initialize canvas
        self._canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self._axes = self._canvas.figure.subplots()
        self.toolbar = NavigationToolbar(self._canvas, self)

        # create controls
        label_normalization = QLabel('normalization:')
        cbox_normalization = QComboBox()
        cbox_normalization.addItems(['max', 'sum', 'raw'])
        cbox_normalization.activated.connect(self._normalization_changed)

        # create layout
        layout_settings = QHBoxLayout()
        layout_settings.addWidget(label_normalization)
        layout_settings.addWidget(cbox_normalization)
        layout_main = QVBoxLayout()
        layout_main.addWidget(self._canvas)
        layout_main.addWidget(self.toolbar)
        layout_main.addLayout(layout_settings)
        self.setLayout(layout_main)

        # define default plotting and layer properties
        self._properties = {
            'active': False,
            'normalization': 'max',
            'upper_bound_normed': 1.05
            }

        # set up callbacks and plot settings for active selection
        self._layer_selection_changed()
        self.viewer.layers.selection.events.changed.connect(self._layer_selection_changed)

        # initialize plot
        (self._line,) = self._axes.plot(range(self._properties['nchannels']), self._properties['spectrum'])


    def _layer_selection_changed(self):
        layer = self.viewer.layers.selection.active
        if layer and isinstance(layer, Image) and layer.ndim > self.viewer.dims.ndisplay:
            # determine effective bit depth
            effective_bit_depth = _utils.effective_bit_depth(layer.data)

            # determine number of spectral channels
            nchannels = layer.data.shape[0]

            # set null spectrum
            spectrum = np.zeros(nchannels)

            # store properties for use in plotting
            self._properties.update({
                'active': True,
                'layer': layer,
                'upper_bound_raw': 2**effective_bit_depth * 1.05,
                'nchannels': nchannels,
                'spectrum': spectrum,
                })
        else:
            self._properties['active'] = False

    
    def _normalization_changed(self, ind):
        if ind == 0:
            self._properties['normalization'] = 'max'
            self._axes.set_ybound(upper=self._properties['upper_bound_normed'])
        elif ind == 1:
            self._properties['normalization'] = 'sum'
            self._axes.set_ybound(upper=self._properties['upper_bound_normed'])
        else:
            self._properties['normalization'] = 'raw'
            self._axes.set_ybound(upper=self._properties['upper_bound_raw'])
        
        self._plot_spectrum()


    def _mouse_moved(self, viewer, event):
        if self._properties['active']:
            layer = self._properties['layer']
            coordinates = layer.world_to_data(self.viewer.cursor.position)
            xy_coordinates = [int(x) for x in coordinates[-2:]]
            if all(xy_coordinates >= layer.corner_pixels[0,-2:]) and all(xy_coordinates < layer.corner_pixels[1,-2:]):
                self._properties['spectrum'] = layer.data[:,xy_coordinates[0], xy_coordinates[1]]
                self._plot_spectrum()


    def _plot_spectrum(self):
        spectrum = self._properties['spectrum']

        if self._properties['normalization'] == 'max':
            spectrum = _utils.safe_normalize_max(spectrum)
            self._axes.set_ybound(upper=1.05)
        elif self._properties['normalization'] == 'sum':
            spectrum = _utils.safe_normalize_sum(spectrum)
            self._axes.set_ybound(upper=1.05)
            
        channels = self._properties['nchannels']
        self._line.set_data(range(channels), spectrum)

        self._axes.figure.canvas.draw()


if __name__ == "__main__":
    import napari
    viewer = napari.Viewer()
    im1 = napari.utils.io.magic_imread('/Users/brossetti/Desktop/Lepto_10fluors_s001.tif')
    im2 = im1.copy() - 1
    viewer.add_image(im1)
    viewer.add_image(im2)
    napari.run()