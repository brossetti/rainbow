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
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox
)

# TODO:
# - Add a method to store spectra
# - Add an export method to save stored spectra as a .ref file
# - Add drag-and-drop function that plots spectra from a .ref file
# - Fix xmin/xmax to work with wavelengths or indices

class InspectionWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        # build interface
        self._setup_interface()

        # define default plotting and layer properties
        self._properties = {
            'active_selection': False,
            'live': True,
            'hidden': False,
            'normalization': 0,
            'ymin': -0.05,
            'ymax': 1.05,
            'xmin': -1.05,
            'xmax': 43.05,
            'axis_limits_stale': False,
            'effective_bit_depth': 0,
            'nchannels': 42,
            'live_spectrum': np.full(42, np.NaN)
        }

        # set up callbacks and plot for active selection
        self._layer_selection_changed()
        self.viewer.layers.selection.events.changed.connect(self._layer_selection_changed)

        # initialize plot
        (self._line,) = self._axes.plot(
            range(self._properties['nchannels']), 
            self._properties['live_spectrum']
        )
        self._axes.set_ybound(
            lower=self._properties['ymin'],
            upper=self._properties['ymax']
        )
        self._axes.set_xbound(
            lower=self._properties['xmin'],
            upper=self._properties['xmax']
        )

        # set plot style
        self._axes.patch.set_color('none')
        self._axes.spines['right'].set_color('none')
        self._axes.spines['top'].set_color('none')
        self._axes.tick_params(axis='both', bottom=False)

        # set up callbacks and plot theme settings
        self._theme_changed()
        self.viewer.events.theme.connect(self._theme_changed)


    def _setup_interface(self):
        self._canvas = FigureCanvas(
            Figure(figsize=(5, 3), facecolor='none', edgecolor='none')
        )
        self._axes = self._canvas.figure.subplots()
        self._toolbar = NavigationToolbar(self._canvas, self)

        # controls
        self._button_live = QPushButton('live')
        self._button_live.setCheckable(True)
        self._button_live.setChecked(True)
        self._button_live.clicked.connect(self._live_toggled)
        self.viewer.bind_key('l', self._live_toggled)
        self._button_hide = QPushButton('hide')
        self._button_hide.setCheckable(True)
        self._button_hide.clicked.connect(self._hide_toggled)
        cbox_normalization = QComboBox()
        cbox_normalization.addItems(['none', 'max', 'sum'])
        cbox_normalization.activated.connect(self._normalization_changed)

        # layout
        layout_settings = QHBoxLayout()
        layout_settings.addWidget(QLabel('inspector:'))
        layout_settings.addWidget(self._button_live)
        layout_settings.addWidget(self._button_hide)
        layout_settings.addStretch(1)
        layout_settings.addWidget(QLabel('normalization:'))
        layout_settings.addWidget(cbox_normalization)
        layout_settings.addStretch(0)

        layout_main = QVBoxLayout()
        layout_main.addWidget(self._canvas)
        layout_main.addWidget(self._toolbar)
        layout_main.addLayout(layout_settings)

        self.setLayout(layout_main)


    def _set_mouse_move_callback(self):
        """Adds the mouse move callback only if settings allow"""
        active_selection = self._properties['active_selection']
        live = self._properties['live']
        hidden = self._properties['hidden']
        already_set = self._mouse_moved in self.viewer.mouse_move_callbacks

        if active_selection and live and not hidden and not already_set:
            self.viewer.mouse_move_callbacks.append(self._mouse_moved)


    def _unset_mouse_move_callback(self):
        """Removes the mouse move callback if it exists"""
        if self._mouse_moved in self.viewer.mouse_move_callbacks:
            self.viewer.mouse_move_callbacks.remove(self._mouse_moved)


    def _layer_selection_changed(self):
        """Modifies state for new active layer"""
        layer = self.viewer.layers.selection.active
        if layer and isinstance(layer, Image) and (layer.ndim > self.viewer.dims.ndisplay):
            # determine effective bit depth
            effective_bit_depth = _utils.effective_bit_depth(layer.data)

            # determine number of spectral channels
            # TODO: dynamically determine correct spectral dimension
            nchannels = layer.data.shape[0]

            # set null spectrum
            spectrum = np.full(nchannels, np.NaN)

            # store properties for use in plotting
            self._properties.update({
                'active_selection': True,
                'layer': layer,
                'xmin': -0.05 - (nchannels * 0.05),
                'xmax': nchannels * 1.05,
                'axis_limits_stale': True,
                'effective_bit_depth': effective_bit_depth,   
                'nchannels': nchannels,
                'live_spectrum': spectrum
            })

            # correct y-axis limits
            self._calculate_ylimits()

            # re-enable live button
            self._button_live.setDisabled(False)

            # conditianally add mouse move callback to viewer
            self._set_mouse_move_callback()
        else:
            # turn everything off since there is no active selection
            self._properties['active_selection'] = False
            self._button_live.setDisabled(True)
            self._unset_mouse_move_callback()


    def _live_toggled(self, viewer):
        """Live/paused live spectrum plotting"""
        if self._properties['live']:
            # pause
            self._button_live.setChecked(False)
            self._properties['live'] = False
            self._unset_mouse_move_callback()
        else:
            # unpause
            self._button_live.setChecked(True)
            self._properties['live'] = True
            self._set_mouse_move_callback()


    def _hide_toggled(self):
        """Hide/Unhide live spectrum"""
        if self._properties['hidden']:
            # unhide
            self._button_live.setDisabled(False)
            self._line.set_linestyle('solid')
            self._properties['hidden'] = False
            self._set_mouse_move_callback()
        else:
            # hide
            self._button_live.setDisabled(True)
            self._line.set_linestyle('None')
            self._properties['hidden'] = True
            self._unset_mouse_move_callback()
        self._canvas.draw()


    def _theme_changed(self):
        """Updates plot for new color theme"""
        theme = get_theme(self.viewer.theme, False)

        # update matplotlib figure
        self._axes.tick_params(axis='both', colors=theme.text.as_hex())
        self._axes.spines['left'].set_color(theme.text.as_hex())
        self._axes.spines['bottom'].set_color(theme.text.as_hex())
        self._line.set_color(theme.icon.as_hex())
        self._canvas.draw()        


    def _calculate_ylimits(self):
        norm = self._properties['normalization']
        if norm == 1 or norm == 2:
            # max or sum
            self._properties.update({
                'ymin': -0.05,
                'ymax': 1.05,
                'axis_limits_stale': True
            })
        else:
            # none
            effective_bit_depth = self._properties['effective_bit_depth']
            self._properties.update({
                'ymin': -0.05 - (2**effective_bit_depth * 0.05),
                'ymax': 2**effective_bit_depth * 1.05,
                'axis_limits_stale': True
            })


    def _normalization_changed(self, idx):
        self._properties['normalization'] = idx
        self._calculate_ylimits()
        self._plot_spectrum()


    def _mouse_moved(self, viewer, event):
        """Plots spectrum if coordinates are inbounds for active layer"""
        layer = self._properties['layer']
        coordinates = layer.world_to_data(self.viewer.cursor.position)
        xy_coordinates = [int(x) for x in coordinates[-2:]]
        if all(xy_coordinates >= layer.corner_pixels[0,-2:]) and all(xy_coordinates < layer.corner_pixels[1,-2:]):
            self._properties['live_spectrum'] = layer.data[:,xy_coordinates[0], xy_coordinates[1]]
            self._plot_spectrum()


    def _plot_spectrum(self):
        """Plots the current spectrum with/without normalization"""
        spectrum = self._properties['live_spectrum']

        if self._properties['normalization'] == 1:
            spectrum = _utils.safe_normalize_max(spectrum)
        elif self._properties['normalization'] == 2:
            spectrum = _utils.safe_normalize_sum(spectrum)
            
        channels = self._properties['nchannels']
        self._line.set_data(range(channels), spectrum)

        if self._properties['axis_limits_stale']:
            self._axes.set_xbound(
                lower=self._properties['xmin'], 
                upper=self._properties['xmax']
            )
            self._axes.set_ybound(
                lower=self._properties['ymin'], 
                upper=self._properties['ymax']
            )
            self._properties['axis_limits_stale'] = False

        self._canvas.draw()


if __name__ == "__main__":
    import napari
    viewer = napari.Viewer()
    im1 = np.random.random((3, 256, 128)) # Z,Y,X order
    im2 = np.random.random((3, 256, 128))
    viewer.add_image(im1)
    viewer.add_image(im2)
    napari.run()