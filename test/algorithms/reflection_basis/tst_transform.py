from __future__ import division

def evaluate_gaussian(x, a, x0, sx):

    from math import exp

    assert(len(x) == len(x0))
    assert(len(x) == len(sx))

    g = 0.0
    for xi, x0i, sxi in zip(x, x0, sx):
        g += (xi - x0i)**2 / (2.0 * sxi**2)
    return a * exp(-g)

def gaussian(size, a, x0, sx):

    from scitbx.array_family import flex

    result = flex.double(flex.grid(size))
    index = [0 for i in range(len(size))]
    while True:
        result[index[::-1]] = evaluate_gaussian(index[::-1], a, x0, sx)
        for j in range(len(size)):
            index[j] += 1
            if index[j] < size[::-1][j]:
                break
            index[j] = 0
            if j == len(size) - 1:
                return result

class TestForward(object):
    def __init__(self, filename):
        from dials.model.serialize import load
        from dials.algorithms.reflection_basis import transform
        from dials.algorithms.shoebox import BBoxCalculator
        from math import pi

        # Load the sweep
        self.sweep = load.sweep(filename)

        # Get the models
        self.beam = self.sweep.get_beam()
        self.detector = self.sweep.get_detector()
        self.gonio = self.sweep.get_goniometer()
        self.scan = self.sweep.get_scan()

#        self.beam.set_direction((0.0, 0.0, 1.0))
#        self.gonio.set_rotation_axis((1.0, 0.0, 0.0))
#        self.detector.set_frame((1.0, 0.0, 0.0),
#                                (0.0, 1.0, 0.0),
#                                (-150, -150, -200))

        # Set some parameters
        self.sigma_divergence =self.beam.get_sigma_divergence(deg=False)
        self.mosaicity = 0.157 * pi / 180
        self.n_sigma = 3
        self.grid_size = 7
        self.delta_divergence = self.n_sigma * self.sigma_divergence

        step_size = self.delta_divergence / self.grid_size
        self.delta_divergence2 = self.delta_divergence + step_size * 0.5
        self.delta_mosaicity = self.n_sigma * self.mosaicity

        # Create the bounding box calculator
        self.calculate_bbox = BBoxCalculator(
            self.beam, self.detector, self.gonio, self.scan,
            self.delta_divergence2,
            self.delta_mosaicity)

        # Initialise the transform
        self.spec = transform.TransformSpec(
            self.beam, self.detector, self.gonio, self.scan,
            self.mosaicity, self.n_sigma, self.grid_size)

    def __call__(self):
        self.tst_conservation_of_counts()
        #self.tst_transformed_centroid()
        self.tst_transform_with_background()

    def tst_conservation_of_counts(self):

        from scitbx import matrix
        from random import uniform
        from dials.algorithms.reflection_basis import CoordinateSystem
        from dials.algorithms.reflection_basis import transform
        from scitbx.array_family import flex
        from time import time

        s0 = self.beam.get_s0()
        m2 = self.gonio.get_rotation_axis()
        s0_length = matrix.col(self.beam.get_s0()).length()

        # Create an s1 map
        s1_map = transform.beam_vector_map(self.detector, self.beam, True)

        for i in range(100):

            # Get random x, y, z
            x = uniform(300, 1800)
            y = uniform(300, 1800)
            z = uniform(-10, 0)

            # Get random s1, phi, panel
            s1 = matrix.col(self.detector.get_pixel_lab_coord(
                (x, y))).normalize() * s0_length
            phi = self.scan.get_angle_from_array_index(z, deg=False)
            panel = 0

            # Calculate the bounding box
            bbox = self.calculate_bbox(s1, phi, panel)
            x0, x1, y0, y1, z0, z1 = bbox

            # Create the coordinate system
            cs = CoordinateSystem(m2, s0, s1, phi)

            # The grid index generator
            step_size = self.delta_divergence / self.grid_size
            grid_index = transform.GridIndexGenerator(cs, x0, y0,
                (step_size, step_size), self.grid_size, s1_map)

            # Create the image
            #image = flex.double(flex.grid(z1 - z0, y1 - y0, x1 - x0), 1)
            image = gaussian((z1 - z0, y1 - y0, x1 - x0), 10.0,
                (z - z0, y - y0, x - x0), (2.0, 2.0, 2.0))
            mask = flex.bool(flex.grid(image.all()), False)
            for j in range(y1 - y0):
                for i in range(x1 - x0):
                    inside = False
                    gx00, gy00 = grid_index(j, i)
                    gx01, gy01 = grid_index(j, i+1)
                    gx10, gy10 = grid_index(j+1, i)
                    gx11, gy11 = grid_index(j+1, i+1)
                    mingx = min([gx00, gx01, gx10, gx11])
                    maxgx = max([gx00, gx01, gx10, gx11])
                    mingy = min([gy00, gy01, gy10, gy11])
                    maxgy = max([gy00, gy01, gy10, gy11])
                    if (mingx >= 0 and maxgx <= 2 * self.grid_size + 1 and
                        mingy >= 0 and maxgy <= 2 * self.grid_size + 1):
                        inside = True
                    for k in range(1, z1 - z0 - 1):
                        mask[k,j,i] = inside

            # Transform the image to the grid
            transformed = transform.Forward(self.spec, cs, bbox, image, mask)
            grid = transformed.profile()

            # Get the sums and ensure they're the same
            eps = 1e-7
            sum_grid = flex.sum(grid)
            sum_image = flex.sum(flex.double(flex.select(image, flags=mask)))
            assert(abs(sum_grid - sum_image) <= eps)

        # Test passed
        print 'OK'

#    def tst_transformed_centroid(self):

#        from scitbx import matrix
#        from random import uniform
#        from dials.algorithms.reflection_basis import CoordinateSystem
#        from dials.algorithms.reflection_basis import transform
#        from scitbx.array_family import flex
#        from time import time

#        s0 = self.beam.get_s0()
#        m2 = self.gonio.get_rotation_axis()
#        s0_length = matrix.col(self.beam.get_s0()).length()

#        # Create an s1 map
#        s1_map = transform.beam_vector_map(self.detector, self.beam, True)

#        # Get random x, y, z
#        x = uniform(300, 1800)
#        y = uniform(300, 1800)
#        z = uniform(-10, 0)

#        # Get random s1, phi, panel
#        s1 = matrix.col(self.detector.get_pixel_lab_coord(
#            (x, y))).normalize() * s0_length
#        phi = self.scan.get_angle_from_array_index(z, deg=False)
#        panel = 0

#        # Calculate the bounding box
#        bbox = self.calculate_bbox(s1, phi, panel)
#        x0, x1, y0, y1, z0, z1 = bbox

#        # Create the coordinate system
#        cs = CoordinateSystem(m2, s0, s1, phi)

#        # The grid index generator
#        step_size = self.delta_divergence / self.grid_size
#        grid_index = transform.GridIndexGenerator(cs, x0, y0,
#            (step_size, step_size), self.grid_size, s1_map)

#        # Create the image
#        image = gaussian((z1 - z0, y1 - y0, x1 - x0), 10.0,
#            (z - z0, y - y0, x - x0), (2.0, 2.0, 2.0))

#        print x, y, z, bbox
#        print (z1 - z0, y1 - y0, x1 - x0), (z - z0, y - y0, x - x0)

#        mask = flex.bool(flex.grid(image.all()), False)
#        for j in range(y1 - y0):
#            for i in range(x1 - x0):
#                inside = False
#                gx00, gy00 = grid_index(j, i)
#                gx01, gy01 = grid_index(j, i+1)
#                gx10, gy10 = grid_index(j+1, i)
#                gx11, gy11 = grid_index(j+1, i+1)
#                mingx = min([gx00, gx01, gx10, gx11])
#                maxgx = max([gx00, gx01, gx10, gx11])
#                mingy = min([gy00, gy01, gy10, gy11])
#                maxgy = max([gy00, gy01, gy10, gy11])
#                if (mingx >= 0 and maxgx <= 2 * self.grid_size + 1 and
#                    mingy >= 0 and maxgy <= 2 * self.grid_size + 1):
#                    inside = True
#                for k in range(1, z1 - z0 - 1):
#                    mask[k,j,i] = inside
#                    #image[k,j,i] *= inside
#        from matplotlib import pylab
#        pylab.imshow(image.as_numpy_array()[(z1 - z0) / 2,:,:], interpolation='none')
#        pylab.show()

#        # Transform the image to the grid
#        grid = self.transform(cs, bbox, image, mask)

#        from matplotlib import pylab
#        pylab.imshow(grid.as_numpy_array()[7,:,:], interpolation='none')
#        pylab.show()

#        # Get the sums and ensure they're the same
#        eps = 1e-7
#        sum_grid = flex.sum(grid)
#        sum_image = flex.sum(flex.double(flex.select(image, flags=mask)))
#        assert(abs(sum_grid - sum_image) <= eps)

#        # Check the centroid
#        sz = self.grid_size * 2 + 1
#        grid_x = flex.double(flex.grid(sz, sz, sz))
#        grid_y = flex.double(flex.grid(sz, sz, sz))
#        grid_z = flex.double(flex.grid(sz, sz, sz))
#        for k in range(sz):
#            for j in range(sz):
#                for i in range(sz):
#                    grid_x[k,j,i] = i + 0.5
#                    grid_y[k,j,i] = j + 0.5
#                    grid_z[k,j,i] = k + 0.5
#
#        sum_grid_x = flex.sum(grid * grid_x)
#        sum_grid_y = flex.sum(grid * grid_y)
#        sum_grid_z = flex.sum(grid * grid_z)
#        xc = sum_grid_x / sum_grid
#        yc = sum_grid_y / sum_grid
#        zc = sum_grid_z / sum_grid
#        print xc, yc, zc
#        assert(abs(xc - self.grid_size + 0.5) <= 0.5)
#        assert(abs(yc - self.grid_size + 0.5) <= 0.5)
#        assert(abs(zc - self.grid_size + 0.5) <= 0.5)

#        # Test passed
#        print 'OK'

    def tst_transform_with_background(self):

        from scitbx import matrix
        from random import uniform
        from dials.algorithms.reflection_basis import CoordinateSystem
        from dials.algorithms.reflection_basis import transform
        from scitbx.array_family import flex
        from time import time

        s0 = self.beam.get_s0()
        m2 = self.gonio.get_rotation_axis()
        s0_length = matrix.col(self.beam.get_s0()).length()

        # Create an s1 map
        s1_map = transform.beam_vector_map(self.detector, self.beam, True)

        for i in range(100):

            # Get random x, y, z
            x = uniform(300, 1800)
            y = uniform(300, 1800)
            z = uniform(-10, 0)

            # Get random s1, phi, panel
            s1 = matrix.col(self.detector.get_pixel_lab_coord(
                (x, y))).normalize() * s0_length
            phi = self.scan.get_angle_from_array_index(z, deg=False)
            panel = 0

            # Calculate the bounding box
            bbox = self.calculate_bbox(s1, phi, panel)
            x0, x1, y0, y1, z0, z1 = bbox

            # Create the coordinate system
            cs = CoordinateSystem(m2, s0, s1, phi)

            # The grid index generator
            step_size = self.delta_divergence / self.grid_size
            grid_index = transform.GridIndexGenerator(cs, x0, y0,
                (step_size, step_size), self.grid_size, s1_map)

            # Create the image
            #image = flex.double(flex.grid(z1 - z0, y1 - y0, x1 - x0), 1)
            image = gaussian((z1 - z0, y1 - y0, x1 - x0), 10.0,
                (z - z0, y - y0, x - x0), (2.0, 2.0, 2.0))
            background = flex.random_double(len(image))
            background.resize(image.accessor())
            mask = flex.bool(flex.grid(image.all()), False)
            for j in range(y1 - y0):
                for i in range(x1 - x0):
                    inside = False
                    gx00, gy00 = grid_index(j, i)
                    gx01, gy01 = grid_index(j, i+1)
                    gx10, gy10 = grid_index(j+1, i)
                    gx11, gy11 = grid_index(j+1, i+1)
                    mingx = min([gx00, gx01, gx10, gx11])
                    maxgx = max([gx00, gx01, gx10, gx11])
                    mingy = min([gy00, gy01, gy10, gy11])
                    maxgy = max([gy00, gy01, gy10, gy11])
                    if (mingx >= 0 and maxgx <= 2 * self.grid_size + 1 and
                        mingy >= 0 and maxgy <= 2 * self.grid_size + 1):
                        inside = True
                    for k in range(1, z1 - z0 - 1):
                        mask[k,j,i] = inside

            # Transform the image to the grid
            transformed = transform.Forward(self.spec, cs, bbox, image, background, mask)
            igrid = transformed.profile()
            bgrid = transformed.background()

            # Get the sums and ensure they're the same
            eps = 1e-7
            sum_igrid = flex.sum(igrid)
            sum_bgrid = flex.sum(bgrid)
            sum_image = flex.sum(flex.double(flex.select(image, flags=mask)))
            sum_bkgrd = flex.sum(flex.double(flex.select(background, flags=mask)))
            assert(abs(sum_igrid - sum_image) <= eps)
            assert(abs(sum_bgrid - sum_bkgrd) <= eps)

        # Test passed
        print 'OK'


#class TestReverse(object):
#    def __init__(self, filename):
#        from dials.model.serialize import load
#        from dials.algorithms.reflection_basis import transform
#        from dials.algorithms.shoebox import BBoxCalculator
#        from math import pi

#        # Load the sweep
#        self.sweep = load.sweep(filename)

#        # Get the models
#        self.beam = self.sweep.get_beam()
#        self.detector = self.sweep.get_detector()
#        self.gonio = self.sweep.get_goniometer()
#        self.scan = self.sweep.get_scan()

#        # Set some parameters
#        self.sigma_divergence =self.beam.get_sigma_divergence(deg=False)
#        self.mosaicity = 0.157 * pi / 180
#        self.n_sigma = 3
#        self.grid_size = 7
#        self.delta_divergence = self.n_sigma * self.sigma_divergence

#        step_size = self.delta_divergence / self.grid_size
#        self.delta_divergence2 = self.delta_divergence + step_size * 0.5
#        self.delta_mosaicity = self.n_sigma * self.mosaicity

#        # Create the bounding box calculator
#        self.calculate_bbox = BBoxCalculator(
#            self.beam, self.detector, self.gonio, self.scan,
#            self.delta_divergence2,
#            self.delta_mosaicity)

#        # Initialise the transform
#        self.transform = transform.Reverse(
#            self.beam, self.detector, self.gonio, self.scan,
#            self.mosaicity, self.n_sigma, self.grid_size)

#    def __call__(self):
#        self.tst_conservation_of_counts()

#    def tst_conservation_of_counts(self):

#        from scitbx import matrix
#        from random import uniform
#        from dials.algorithms.reflection_basis import CoordinateSystem
#        from dials.algorithms.reflection_basis import transform
#        from scitbx.array_family import flex
#        from time import time

#        s0 = self.beam.get_s0()
#        m2 = self.gonio.get_rotation_axis()
#        s0_length = matrix.col(self.beam.get_s0()).length()

#        # Create an s1 map
#        s1_map = transform.beam_vector_map(self.detector, self.beam, True)

#        for i in range(100):

#            # Get random x, y, z
#            x = uniform(300, 1800)
#            y = uniform(300, 1800)
#            z = uniform(-10, 0)

#            # Get random s1, phi, panel
#            s1 = matrix.col(self.detector.get_pixel_lab_coord(
#                (x, y))).normalize() * s0_length
#            phi = self.scan.get_angle_from_array_index(z, deg=False)
#            panel = 0

#            # Calculate the bounding box
#            bbox = self.calculate_bbox(s1, phi, panel)
#            x0, x1, y0, y1, z0, z1 = bbox

#            # Create the coordinate system
#            cs = CoordinateSystem(m2, s0, s1, phi)

#            # Create the image
#            #image = flex.double(flex.grid(z1 - z0, y1 - y0, x1 - x0), 1)
#            sz = self.grid_size * 2 + 1
#            ct = self.grid_size + 0.5
#            grid = gaussian((sz, sz, sz), 10.0,
#                (ct, ct, ct), (2.0, 2.0, 2.0))

#            # Transform the image to the grid
#            image = self.transform(cs, bbox, grid)

#            # Get the sums and ensure they're the same
#            eps = 1e-7
#            sum_grid = flex.sum(grid)
#            sum_image = flex.sum(image)
#            assert(abs(sum_grid - sum_image) <= eps)

#        # Test passed
#        print 'OK'


class Test(object):
    def __init__(self):

        import os
        import libtbx.load_env

        try:
            dials_regression = libtbx.env.dist_path('dials_regression')
        except KeyError, e:
            print 'FAIL: dials_regression not configured'
            return

        # Set the sweep filename and load the sweep
        filename = os.path.join(
            dials_regression,
            'centroid_test_data',
            'sweep.json')

        self.tst_forward = TestForward(filename)
        #self.tst_reverse = TestReverse(filename)

    def run(self):
        self.tst_forward()
        #self.tst_reverse()


if __name__ == '__main__':
    test = Test()
    test.run()
