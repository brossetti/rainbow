import _utils

import numpy as np

class Spectrum():
    def __init__(self, name, wavelengths, data):
        self.name = name
        self.wavelengths = wavelengths
        self.data = data

    
    def normalize(self):
        self.data = _utils.safe_normalize_max(self.data)


    def interp_spectrum(self, interp_wavelengths):
        return np.interp(interp_wavelengths, self.wavelengths, self.data)
        