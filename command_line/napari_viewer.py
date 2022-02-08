import dask
import dask.array
import napari
import numpy

from dials.util.options import ArgumentParser, flatten_experiments


def run(args=None):
    usage = "dials.napari_viewer [options] data.nxs/data_????.cbf"

    parser = ArgumentParser(
        usage=usage,
        read_experiments=True,
        read_experiments_from_images=True,
    )

    params, options = parser.parse_args(args, show_diff_phil=True)
    experiments = flatten_experiments(params.input.experiments)

    assert len(experiments) == 1

    images = experiments[0].imageset

    def _reader(n):
        image = images.get_raw_data(n)[0].as_numpy_array()
        ny, nx = image.shape
        return numpy.reshape(image, (1, ny, nx))

    # load the first image to get the information we need
    i0 = _reader(0)

    nn = len(images)
    lazy_images = [dask.delayed(_reader)(n) for n in range(nn)]
    lazy_array = dask.array.concatenate(
        [
            dask.array.from_delayed(i, shape=i0.shape, dtype=i0.dtype)
            for i in lazy_images
        ],
        axis=0,
    )

    assert lazy_array.shape[0] == nn

    _ = napari.view_image(
        lazy_array, title="DIALS image viewer", contrast_limits=[0, 10]
    )
    napari.run()


run()
