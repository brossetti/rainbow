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

        # metadata
        self._layer_metadata = {
            'x': None,
            'y': None,
            'z': None,
            'c': None
        }

        # spatial dimensions
        self._layout_dimensions = QGridLayout()
        layout_main = QVBoxLayout()
        layout_main.addLayout(self._layout_dimensions)

        self.setLayout(layout_main)

        # determine metadata for current selection
        self._layer_changed()
        self.viewer.layers.selection.events.changed.connect(self._layer_changed)
        self.viewer.dims.events.order.connect(self._layer_changed)
        self.viewer.dims.events.ndisplay.connect(self._layer_changed)


    def _display_dimensions(self, layer):
        self._clear_metadata_display()
        s = layer.data.shape
        i = 0
        for d in ['x', 'y', 'z']:
            if self._layer_metadata[d] is not None:
                label = QLabel(d.upper() + ': ' + str(s[self._layer_metadata[d]]))
                self._layout_dimensions.addWidget(label, 0, i)
                i += 1
        
        if len(self.viewer.dims.not_displayed) == 1:
            # assume this one non-displayed dimension represent spectral channels
            label = QLabel('C: ' + str(s[self._layer_metadata['c']]))
            self._layout_dimensions.addWidget(label, 0, i)
        else:
            # make radio buttons if more than one non-displayed dimension
            pass



    def _identify_dimensions(self, layer):
        # identify X and Y
        self._layer_metadata['x'] = self.viewer.dims.displayed[-1]
        self._layer_metadata['y'] = self.viewer.dims.displayed[-2]

        # identify Z if it exists
        if len(self.viewer.dims.displayed) == 3:
            self._layer_metadata['z'] = self.viewer.dims.displayed[-3]
        else:
            self._layer_metadata['z'] = None

        # identify C
        if layer.ndim > self.viewer.dims.ndisplay:
            if self._layer_metadata['c'] not in self.viewer.dims.not_displayed:
                # assume first of non-displayed dimensions is channel
                self._layer_metadata['c'] = self.viewer.dims.not_displayed[0]


    def _clear_metadata_display(self):
        while self._layout_dimensions.count():
            child = self._layout_dimensions.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


    def _layer_changed(self):
        """Modifies state for new active layer"""
        layer = self.viewer.layers.selection.active
        if layer and isinstance(layer, Image):
            self._identify_dimensions(layer)
            self._display_dimensions(layer)
        else:
            self._clear_metadata_display()


if __name__ == "__main__":
    import napari
    viewer = napari.Viewer()
    im1 = np.random.random((10, 5, 256, 128)) # Z,Y,X order
    im2 = np.random.random((3, 256, 128))
    viewer.add_image(im1)
    viewer.add_image(im2)
    napari.run()