import _utils
import numpy as np
from napari.layers import Image
from napari.utils.theme import get_theme
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
from qtpy.QtGui import QIcon, QColor
from qtpy.QtWidgets import (
    QWidget,
    QStyle, 
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox
)

# TODO:
# - Add Live button starts/stops plotting by adding/removing mouse_move_callback from viewer
# - Add a method to store spectra
# - Add an export method to save stored spectra as a .ref file
# - Add drag-and-drop function that plots spectra from a .ref file

# BUG:
# - Starting with no active layer selection will result in a 'nchannels' KeyError at line 77


class InspectionWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        # initialize canvas
        self._canvas = FigureCanvas(
            Figure(figsize=(5, 3), facecolor='none', edgecolor='none')
        )
        self._axes = self._canvas.figure.subplots()
        self._toolbar = NavigationToolbar(self._canvas, self)

        # create controls
        self._button_freeze = QPushButton('Freeze')
        icon_play = self.style().standardPixmap(QStyle.SP_MediaPlay)
        icon_pause = self.style().standardIcon(QStyle.SP_MediaPause)
        self._button_freeze.setIcon(QIcon(icon_play))
        self._button_freeze.clicked.connect(self._frozen_unfrozen)
        button_hide = QPushButton('Hide')
        # button_freeze.setCheckable(True)
        label_normalization = QLabel('normalization:')
        cbox_normalization = QComboBox()
        cbox_normalization.addItems(['none', 'max', 'sum'])
        cbox_normalization.activated.connect(self._normalization_changed)

        # create layout
        layout_settings = QHBoxLayout()
        layout_settings.addWidget(self._button_freeze)
        layout_settings.addWidget(button_hide)
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
            'frozen': False,
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


    def _frozen_unfrozen(self):
        if self._properties['frozen']:
            # add mouse move callback to viewer
            if self._mouse_moved not in self.viewer.mouse_move_callbacks:
                self.viewer.mouse_move_callbacks.append(self._mouse_moved)
            self._properties['frozen'] = False
            self._button_freeze.setText('Freeze')
        else:
            # remove mouse move callback from viewer
            if self._mouse_moved in self.viewer.mouse_move_callbacks:
                self.viewer.mouse_move_callbacks.remove(self._mouse_moved)
            self._properties['frozen'] = True
            self._button_freeze.setText('Unfreeze')


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
            # add mouse move callback to viewer
            if self._mouse_moved not in self.viewer.mouse_move_callbacks:
                self.viewer.mouse_move_callbacks.append(self._mouse_moved)

            # re-enable freeze and hide buttons
            self._button_freeze.setDisabled(False)

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
            if self._mouse_moved in self.viewer.mouse_move_callbacks:
                self.viewer.mouse_move_callbacks.remove(self._mouse_moved)
            self._properties['active'] = False
            self._button_freeze.setDisabled(True)

    
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