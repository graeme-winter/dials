from __future__ import absolute_import, division, print_function

import iotbx.detectors

# store default ImageFactory function
defaultImageFactory = iotbx.detectors.ImageFactory


def SlipViewerImageFactory(filename):
    try:
        return NpyImageFactory(filename)
    except Exception:
        return defaultImageFactory(filename)


# Use the dx2 class as it handles all possible variance of NPY images
def NpyImageFactory(filename):
    from dx2.format.FormatPYunspecified import FormatPYunspecified

    img = FormatPYunspecified(filename)
    return img.get_detectorbase()
