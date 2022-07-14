import _utils

import numpy as np

from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
# from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton
)


class InspectionWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

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

        # define default plot settings
        self._settings = {
            'normalization': 'max',
            'upper_bound_normed': 1.05,
            }

        self._layer_properties = {}

        # set up callbacks and plot settings for current selections
        self._layer_selection_changed()
        self.viewer.layers.selection.events.changed.connect(self._layer_selection_changed)


    def _layer_selection_changed(self, event=None):
        for layer in self.viewer.layers:
            # ensure layer is an image of appropriate dimensions
            if layer._type_string == 'image' and layer.ndim > self.viewer.dims.ndisplay:
                layer_id = id(layer)

                if layer in self.viewer.layers.selection:
                    # add mouse move callback to all selected layers
                    if self._mouse_moved not in layer.mouse_move_callbacks:
                        layer.mouse_move_callbacks.append(self._mouse_moved)
                    
                        # determine effective bit depth
                        effective_bit_depth = _utils.effective_bit_depth(layer.data)

                        # determine number of spectral channels
                        nchannels = layer.data.shape[0]

                        # set null spectrum
                        spectrum = np.zeros(nchannels)

                        # plot null spectrum
                        line = self._axes.plot(spectrum)

                        # store layer properties for later
                        self._layer_properties[layer_id] = {
                            'effective_bit_depth': effective_bit_depth,
                            'nchannels': nchannels,
                            'spectrum': spectrum,
                            'line': line
                            }
  
                elif self._mouse_moved in layer.mouse_move_callbacks:
                    # remove mouse move callback if layer has been unselected
                    layer.mouse_move_callbacks.remove(self._mouse_moved)

                    # remove line from plot
                    self._axes.lines.remove(self._layer_properties[layer_id]['line'][0])
                    
                    # remove layer from properties dictionary
                    del self._layer_properties[layer_id]
            
        # define upper bound for raw data
        max_bit_depth = np.max([self._layer_properties[id]['effective_bit_depth'] for id in self._layer_properties])
        max_nchannels = np.max([self._layer_properties[id]['nchannels'] for id in self._layer_properties])

        self._settings.update({
            'upper_bound_raw': 2**max_bit_depth * 1.05,
            'nchannels': max_nchannels
            })

    
    def _normalization_changed(self, ind):
        if ind == 0:
            self._settings['normalization'] = 'max'
            self._axes.set_ybound(upper=self._settings['upper_bound_normed'])
        elif ind == 1:
            self._settings['normalization'] = 'sum'
            self._axes.set_ybound(upper=self._settings['upper_bound_normed'])
        else:
            self._settings['normalization'] = 'raw'
            self._axes.set_ybound(upper=self._settings['upper_bound_raw'])
        
        for layer_id in self._layer_properties:
            self._plot_layer_spectrum(layer_id)


    def _mouse_moved(self, layer, event):
        coordinates = layer.world_to_data(self.viewer.cursor.position)
        xy_coordinates = [int(x) for x in coordinates[-2:]]
        if all(xy_coordinates >= layer.corner_pixels[0,-2:]) and all(xy_coordinates < layer.corner_pixels[1,-2:]):
            layer_id = id(layer)
            self._layer_properties[layer_id]['spectrum'] = layer.data[:,xy_coordinates[0], xy_coordinates[1]]
            self._plot_layer_spectrum(layer_id)


    def _plot_layer_spectrum(self, layer_id):
        spectrum = self._layer_properties[layer_id]['spectrum']

        if self._settings['normalization'] == 'max':
            spectrum = _utils.safe_normalize_max(spectrum)
            self._axes.set_ybound(upper=1.05)
        elif self._settings['normalization'] == 'sum':
            spectrum = _utils.safe_normalize_sum(spectrum)
            self._axes.set_ybound(upper=1.05)
            
        channels = self._layer_properties[layer_id]['nchannels']
        line = self._layer_properties[layer_id]['line']
        line[0].set_data(range(channels), spectrum)

        line[0].figure.canvas.draw()


if __name__ == "__main__":
    import napari
    viewer = napari.Viewer()
    im1 = napari.utils.io.magic_imread('/Users/brossetti/Desktop/Lepto_10fluors_s001.tif')
    im2 = im1.copy() - 1
    viewer.add_image(im1)
    viewer.add_image(im2)
    napari.run()