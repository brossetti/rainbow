import _utils
import spectrum
import csv
import numpy as np
from scipy.optimize import nnls
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
    QFileDialog,
    QLabel,
    QPushButton,
    QComboBox
)

class UnmixingWidget(QWidget):
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        # initialize canvas
        self._canvas = FigureCanvas(
            Figure(figsize=(5, 3), facecolor='none', edgecolor='none')
        )
        self._axes = self._canvas.figure.subplots()
        self._toolbar = NavigationToolbar(self._canvas, self)

        # controls
        self._button_import = QPushButton('import')
        self._button_import.clicked.connect(self._import_endmembers)
        self._button_unmix = QPushButton('unmix')
        self._button_unmix.clicked.connect(self._unmix)

        # layout
        layout_main = QVBoxLayout()
        layout_main.addWidget(self._canvas)
        layout_main.addWidget(self._toolbar)
        layout_main.addWidget(self._button_import)
        layout_main.addWidget(self._button_unmix)
        self.setLayout(layout_main)

        # define default plotting and layer properties
        self._properties = {
            'ymin': -0.05,
            'ymax': 1.05,
            'xmin': -1.05,
            'xmax': 43.05
        }

        # set up callbacks and plot for active selection
        self._set_unmix_button()
        self.viewer.layers.selection.events.changed.connect(self._set_unmix_button)

        # initialize plot
        self._axes.plot(range(42), np.full(42,np.NaN))

        # set plot style
        self._axes.patch.set_color('none')
        self._axes.spines['right'].set_color('none')
        self._axes.spines['top'].set_color('none')
        self._axes.tick_params(axis='both', bottom=False)

        # set up callbacks and plot theme settings
        self._theme_changed()
        self.viewer.events.theme.connect(self._theme_changed)

    
    def _set_unmix_button(self):
        layer = self.viewer.layers.selection.active
        if layer and isinstance(layer, Image) and (layer.ndim > self.viewer.dims.ndisplay) and self._endmembers:
            self._button_unmix.setEnabled(True)
        else:
            self._button_unmix.setDisabled(True)


    def _import_endmembers(self, viewer):
        """Prompts user to choose an endmember file and loads it"""
        fname,ftype = QFileDialog.getOpenFileName(self, 
            caption='Open file', 
            filter='CSV (*.csv)'
        )

        # load the file
        with open(fname, 'r', newline='') as f:
            csv_reader = csv.reader(f, delimiter=',')
            header = next(csv_reader)
            self._endmembers = []
            for name in header[1:]:
                self._endmembers.append(spectrum.Spectrum(name, [], []))

            for row in csv_reader:
                ncols = len(row)
                for i in range(len(self._endmembers)):
                    self._endmembers[i].wavelengths.append(float(row[0]))
                    if i + 1 < ncols and row[i+1]:
                        self._endmembers[i].data.append(float(row[i+1]))
                    else:
                        self._endmembers[i].data.append(0.0)
            
            for endmember in self._endmembers:
                endmember.wavelengths = np.array(endmember.wavelengths)
                endmember.data = np.array(endmember.data)
                endmember.normalize()

        self._plot_endmembers()
        self._set_unmix_button()


    def _plot_endmembers(self):
        self._axes.cla()
        for endmember in self._endmembers:
            self._axes.plot(endmember.wavelengths, endmember.data)
        self._axes.patch.set_color('none')
        self._canvas.draw()


    def _unmix(self):
        pass

    def _theme_changed(self):
        """Updates plot for new color theme"""
        theme = get_theme(self.viewer.theme, False)

        # update matplotlib figure
        self._axes.tick_params(axis='both', colors=theme.text.as_hex())
        self._axes.spines['left'].set_color(theme.text.as_hex())
        self._axes.spines['bottom'].set_color(theme.text.as_hex())
        self._canvas.draw()        



if __name__ == "__main__":
    import napari
    viewer = napari.Viewer()
    # im1 = napari.utils.io.magic_imread('/Users/brossetti/Desktop/Lepto_10fluors_s001.tif')
    # im2 = im1.copy() - 1
    im1 = np.random.random((3, 256, 128)) # Z,Y,X order
    im2 = np.random.random((3, 256, 128))
    viewer.add_image(im1)
    viewer.add_image(im2)
    napari.run()