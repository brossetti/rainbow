from re import L
import _utils
import numpy as np
from napari.layers import Image
from qtpy.QtWidgets import (
    QWidget,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QComboBox
)

# TODO:
# - Dyanmically display dimensions

class MetadataWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        # build interface
        self._setup_interface()

        # determine metadata for current selection
        self._layer_selection_changed()
        
        # update metadata/display when selection or view is changed
        self.viewer.layers.selection.events.changed.connect(self._layer_selection_changed)
        self.viewer.dims.events.order.connect(self._view_changed)
        self.viewer.dims.events.ndisplay.connect(self._view_changed)


    def _setup_interface(self):
        # controls
        self._cbox_spectral_dimension = QComboBox()
        self._cbox_spectral_dimension.activated.connect(self._spectral_dimension_changed)
        self._sbox_start_wavelength = QDoubleSpinBox()
        self._sbox_start_wavelength.setRange(0,1000)
        self._sbox_start_wavelength.setDecimals(1)
        self._sbox_start_wavelength.valueChanged.connect(self._wavelength_range_changed)
        self._sbox_end_wavelength = QDoubleSpinBox()
        self._sbox_end_wavelength.setRange(0,1000)
        self._sbox_end_wavelength.setDecimals(1)
        self._sbox_end_wavelength.valueChanged.connect(self._wavelength_range_changed)
        self._units_options = ['ch', 'nm']
        self._cbox_units = QComboBox()
        self._cbox_units.addItems(self._units_options)
        self._cbox_units.activated.connect(self._units_changed)

        # layout
        self._layout_axes = QGridLayout()
        layout_spectral_dimension = QHBoxLayout()
        layout_spectral_dimension.addWidget(QLabel('spectral dimension:'))
        layout_spectral_dimension.addWidget(self._cbox_spectral_dimension)
        layout_wavelength_range = QHBoxLayout()
        layout_wavelength_range.addWidget(QLabel('wavelength range:'))
        layout_wavelength_range.addWidget(self._sbox_start_wavelength)
        layout_wavelength_range.addWidget(QLabel(' - '))
        layout_wavelength_range.addWidget(self._sbox_end_wavelength)
        layout_wavelength_range.addWidget(self._cbox_units)

        layout_main = QVBoxLayout()
        layout_main.addLayout(self._layout_axes)
        layout_main.addLayout(layout_spectral_dimension)
        layout_main.addLayout(layout_wavelength_range)

        self.setLayout(layout_main)


    def _spectral_dimension_changed(self, idx):
        pass


    def _wavelength_range_changed(self):
        pass


    def _units_changed(self):
        pass


    def _layer_selection_changed(self):
        """Initializes or gets metadata for new layer selection"""
        self._clear_display()

        # only proceed if there is an active image layer
        layer = self.viewer.layers.selection.active
        if layer and isinstance(layer, Image):
            if 'rainbow' not in layer.metadata:
                layer.metadata['rainbow'] = {} 
            
            if 'axes' not in layer.metadata['rainbow']:
                layer.metadata['rainbow']['axes'] = {'x': {}, 'y': {}, 'z': {}, 'c': {}} 
                self._infer_axis_indices(layer)

            if 'wavelengths' not in layer.metadata['rainbow']:
                layer.metadata['rainbow']['wavelengths'] = list(range(layer.metadata['rainbow']['axes']['c']['extent']))
                layer.metadata['rainbow']['units'] = 'ch'

            self._update_display(layer)


    def _view_changed(self):
        """Update axis labels for all layers with metadata"""
        for layer in self.viewer.layers:
            if 'rainbow' in layer.metadata and 'axes' in layer.metadata['rainbow']:
                self._infer_axis_indices(layer)

                # update display if this is the active layer
                if layer == self.viewer.layers.selection.active:
                    self._update_display(layer)


    def _infer_axis_indices(self, layer):
        """Infers the label for each axis based on the user's current data orientation"""
        axes = layer.metadata['rainbow']['axes']

        # identify X and Y (assume last two)
        axes['x']['index'] = layer._dims_displayed[-1]
        axes['y']['index'] = layer._dims_displayed[-2]

        # identify Z if it exists (assume third to last if in 3D mode)
        if self.viewer.dims.ndisplay == 3 and layer.ndim > 2:
            axes['z']['index'] = layer._dims_displayed[-3]
        else:
            axes['z']['index'] = None

        # identify C (assume first non-displayed dimension)
        if 'index' not in axes['c'] or axes['c']['index'] is None or axes['c']['index'] not in layer._dims_not_displayed:
            if self.viewer.dims.ndisplay < layer.ndim:
                axes['c']['index'] = layer._dims_not_displayed[-1]
            else:
                axes['c']['index'] = None

        # determine extent for each axis
        for a in axes:
            if axes[a]['index'] is None:
                axes[a]['extent'] = 1
            else:
                axes[a]['extent'] = layer.data.shape[axes[a]['index']]


    def _update_display(self, layer):
        """Displays metadata for given layer"""
        self._clear_display()

        # handle displayed axes
        i = 0
        axes = layer.metadata['rainbow']['axes']
        for a in ['x', 'y', 'z']:
            if axes[a]['index'] is not None:
                label = QLabel('%c: %i' % (a.upper(), axes[a]['extent']))
                self._layout_axes.addWidget(label, i//3, i%3)
                i += 1

        # handle non-displayed axes
        if len(layer._dims_not_displayed) == 1:
            # assume this one non-displayed dimension represent spectral channels
            label = QLabel('C: %i' % axes['c']['extent'])
            self._layout_axes.addWidget(label, i//3, i%3)
            self._cbox_spectral_dimension.addItem('C')
        else:
            # make radio buttons if more than one non-displayed dimension
            for n, idx in enumerate(layer._dims_not_displayed):
                if idx == axes['c']['index']:
                    label = QLabel('C: %i' % axes['c']['extent'])
                    self._cbox_spectral_dimension.addItem('C')
                    self._cbox_spectral_dimension.setCurrentIndex(0)
                else:
                    label = QLabel('D%i: %i' % (n, layer.data.shape[idx]))
                    self._cbox_spectral_dimension.addItem('D%i' % n)

                self._layout_axes.addWidget(label, i//3, i%3)
                i += 1

        # update wavelength range
                


    def _clear_display(self):
        """Removes all displayed metadata"""
        # remove dimension display
        while self._layout_axes.count():
            child = self._layout_axes.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # reset spectral dimension cbox
        self._cbox_spectral_dimension.clear()

        # reset wavelength range
        self._sbox_start_wavelength.setValue(0)
        self._sbox_end_wavelength.setValue(0)
        self._cbox_units.clear()


if __name__ == "__main__":
    import napari
    viewer = napari.Viewer()
    im1 = np.random.random((10, 5, 256, 128)) # Z,Y,X order
    im2 = np.random.random((3, 256, 128))
    viewer.add_image(im1)
    viewer.add_image(im2)
    napari.run()