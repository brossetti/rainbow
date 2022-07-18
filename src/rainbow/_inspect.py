import _utils
import numpy as np
from napari.layers import Image
from napari.utils.theme import get_theme
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

# TODO:
# - Add Live button starts/stops plotting by adding/removing mouse_move_callback from viewer
# - Add a method to store spectra
# - Add an export method to save stored spectra as a .ref file
# - Add drag-and-drop function that plots spectra from a .ref file


class InspectionWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        # add mouse move callback to viewer
        self.viewer.mouse_move_callbacks.append(self._mouse_moved)

        # initialize canvas
        self._canvas = FigureCanvas(Figure(figsize=(5, 3), facecolor='none', edgecolor='none'))
        self._axes = self._canvas.figure.subplots()
        self._toolbar = NavigationToolbar(self._canvas, self)

        # create controls
        label_normalization = QLabel('normalization:')
        cbox_normalization = QComboBox()
        cbox_normalization.addItems(['none', 'max', 'sum'])
        cbox_normalization.activated.connect(self._normalization_changed)

        # create layout
        layout_settings = QHBoxLayout()
        layout_settings.addWidget(label_normalization)
        layout_settings.addWidget(cbox_normalization)
        layout_main = QVBoxLayout()
        layout_main.addWidget(self._canvas)
        layout_main.addWidget(self._toolbar)
        layout_main.addLayout(layout_settings)
        self.setLayout(layout_main)

        # define default plotting and layer properties
        self._properties = {
            'active': False,
            'normalization': 'none',
            'upper_bound_normed': 1.05,
            'lower_bound': -0.05
            }

        # set up callbacks and plot for active selection
        self._layer_selection_changed()
        self.viewer.layers.selection.events.changed.connect(self._layer_selection_changed)

        # initialize plot
        (self._line,) = self._axes.plot(range(self._properties['nchannels']), self._properties['spectrum'])
        self._axes.set_ybound(lower=self._properties['lower_bound'], upper=self._properties['upper_bound_raw'])
        
        # set plot style
        self._axes.patch.set_color('none')
        self._axes.spines['right'].set_color('none')
        self._axes.spines['top'].set_color('none')
        self._axes.tick_params(axis='both', bottom=False)

        # set up callbacks and plot theme settings
        self._theme_changed()
        self.viewer.events.theme.connect(self._theme_changed)


    def _theme_changed(self):
        theme = get_theme(self.viewer.theme, False)
        self._axes.tick_params(axis='both', colors=theme.text.as_hex()) # tick marks
        self._axes.spines['left'].set_color(theme.text.as_hex())
        self._axes.spines['bottom'].set_color(theme.text.as_hex())
        self._line.set_color(theme.icon.as_hex())
        self._canvas.draw()        


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

    
    def _normalization_changed(self, idx):
        if idx == 1:
            self._properties['normalization'] = 'max'
            self._axes.set_ybound(lower=self._properties['lower_bound'], upper=self._properties['upper_bound_normed'])
        elif idx == 2:
            self._properties['normalization'] = 'sum'
            self._axes.set_ybound(lower=self._properties['lower_bound'], upper=self._properties['upper_bound_normed'])
        else:
            self._properties['normalization'] = 'none'
            self._axes.set_ybound(lower=self._properties['lower_bound'], upper=self._properties['upper_bound_raw'])
        
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
        elif self._properties['normalization'] == 'sum':
            spectrum = _utils.safe_normalize_sum(spectrum)
            
        channels = self._properties['nchannels']
        self._line.set_data(range(channels), spectrum)

        self._canvas.draw()


if __name__ == "__main__":
    import napari
    viewer = napari.Viewer()
    im1 = napari.utils.io.magic_imread('/Users/brossetti/Desktop/Lepto_10fluors_s001.tif')
    im2 = im1.copy() - 1
    viewer.add_image(im1)
    viewer.add_image(im2)
    napari.run()