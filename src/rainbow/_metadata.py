from re import L
import _utils
import numpy as np
from napari.layers import Image
from qtpy.QtWidgets import (
    QWidget,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox
)

# TODO:
# - Dyanmically display dimensions

class MetadataWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        # layout
        self._layout_dimensions = QGridLayout()
        layout_main = QVBoxLayout()
        layout_main.addLayout(self._layout_dimensions)

        self.setLayout(layout_main)

        # determine metadata for current selection
        self._layer_selection_changed()
        self.viewer.layers.selection.events.changed.connect(self._layer_selection_changed)
        
        # update metadata when view is changed
        self.viewer.dims.events.order.connect(self._view_changed)
        self.viewer.dims.events.ndisplay.connect(self._view_changed)


    def _layer_selection_changed(self):
        """Initializes or gets metadata for new layer selection"""
        layer = self.viewer.layers.selection.active
        self._reset_display()
        if layer and isinstance(layer, Image):
            if 'rainbow' not in layer.metadata:
                layer.metadata['rainbow'] = {} 
            
            if 'axes' not in layer.metadata['rainbow']:
                layer.metadata['rainbow']['axes'] = {'x': {}, 'y': {}, 'z': {}, 'c': {}} 
                self._infer_axis_indices(layer)

            self._display_dimensions(layer)


    def _view_changed(self):
        """Update axis labels for all layers with metadata"""
        for layer in self.viewer.layers:
            if 'rainbow' in layer.metadata and 'axes' in layer.metadata['rainbow']:
                self._infer_axis_indices(layer)

                # update display if this is the active layer
                if layer == self.viewer.layers.selection.active:
                    self._display_dimensions(layer)


    def _infer_axis_indices(self, layer):
        axes = layer.metadata['rainbow']['axes']
        offset = self.viewer.dims.ndim - layer.ndim

        # identify X and Y (assume last two)
        axes['x']['index'] = self.viewer.dims.displayed[-1] - offset
        axes['y']['index'] = self.viewer.dims.displayed[-2] - offset

        # identify Z if it exists (assume third to last if in 3D mode)
        if self.viewer.dims.ndisplay == 3 and layer.ndim > 2:
            axes['z']['index'] = self.viewer.dims.displayed[-3] - offset
        else:
            axes['z']['index'] = -1

        # identify C (assume first non-displayed dimension)
        if 'index' not in axes['c'] or axes['c']['index'] is None or (axes['c']['index'] + offset) not in self.viewer.dims.not_displayed:
            if self.viewer.dims.ndisplay < layer.ndim:
                axes['c']['index'] = max(self.viewer.dims.not_displayed) - offset
            else:
                axes['c']['index'] = -1

        # determine extent for each axis
        for a in axes:
            if axes[a]['index'] < 0:
                axes[a]['index'] = None
                axes[a]['extent'] = 0
            else:
                axes[a]['extent'] = layer.data.shape[axes[a]['index']]


    def _display_dimensions(self, layer):
        self._reset_display()
        axes = layer.metadata['rainbow']['axes']
        i = 0
        for a in ['x', 'y', 'z']:
            if axes[a]['index'] is not None:
                label = QLabel(a.upper() + ': ' + str(axes[a]['extent']))
                self._layout_dimensions.addWidget(label, 0, i)
                i += 1
        
        if self.viewer.dims.ndisplay + 1 == layer.data.ndim:
            # assume this one non-displayed dimension represent spectral channels
            label = QLabel('C: ' + str(str(axes['c']['extent'])))
            self._layout_dimensions.addWidget(label, 0, i)
        else:
            # make radio buttons if more than one non-displayed dimension
            pass


    def _reset_display(self):
        while self._layout_dimensions.count():
            child = self._layout_dimensions.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


if __name__ == "__main__":
    import napari
    viewer = napari.Viewer()
    im1 = np.random.random((10, 5, 256, 128)) # Z,Y,X order
    im2 = np.random.random((3, 256, 128))
    viewer.add_image(im1)
    viewer.add_image(im2)
    napari.run()