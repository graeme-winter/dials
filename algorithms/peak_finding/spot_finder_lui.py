#
# __init__.py
#
#  Copyright (C) 2013 Diamond Light Source
#
#  Author: James Parkhurst & Luis Fuentes Montero
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.
from __future__ import division
from dials.interfaces.peak_finding import SpotFinderInterface
from dials.algorithms.peak_finding.lui_find_peak import *
class SpotFinderLui(SpotFinderInterface):
    '''An interface specification for spot finding classes.'''

    def __init__(self, **kwargs):
        '''Initialise the algorithm with some parameters.

        Params:
            kwargs Key word arguments

        '''
        pass

    def __call__(self, sweep):
        '''The main function of the spot finder. Select the pixels from
        the sweep and then group the pixels into spots. Return the data
        in the form of a reflection list.

        Params:
            sweep The sweep object

        Returns:
            The reflection list

        '''
        x_from_lst, x_to_lst, y_from_lst, y_to_lst, z_from_lst, z_to_lst = do_all_3d(sweep)
        reflection_list = _create_reflection_list(x_from_lst, x_to_lst, y_from_lst, y_to_lst, z_from_lst, z_to_lst)

        for r_lst in reflection_list:
            print r_lst

def do_all_3d(sweep):

    import numpy
    array_3d = sweep.to_array()
    data3d = array_3d.as_numpy_array()
    n_frm = numpy.size(data3d[:, 0:1, 0:1])
    n_row = numpy.size(data3d[0:1, :, 0:1])
    n_col = numpy.size(data3d[0:1, 0:1, :])

    print "n_frm,n_row,n_col", n_frm, n_row, n_col

    #dif3d = numpy.zeros(n_row * n_col * n_frm , dtype = int).reshape(n_frm, n_row, n_col)

    dif3d = numpy.zeros_like(data3d)

    n_blocks_x = 5
    n_blocks_y = 12
    col_block_size = n_col / n_blocks_x
    row_block_size = n_row / n_blocks_y

    for frm_tmp in range(n_frm):
        for tmp_block_x_pos in range(n_blocks_x):
            for tmp_block_y_pos in range(n_blocks_y):

                col_from = int(tmp_block_x_pos * col_block_size)
                col_to = int((tmp_block_x_pos + 1) * col_block_size)
                row_from = int(tmp_block_y_pos * row_block_size)
                row_to = int((tmp_block_y_pos + 1) * row_block_size)

                tmp_dat2d = numpy.copy(data3d[frm_tmp, row_from:row_to, col_from:col_to])
                tmp_dif = find_mask_2d(tmp_dat2d, 5)
                dif3d[frm_tmp, row_from:row_to, col_from:col_to] = tmp_dif

    dif_3d_ext = find_ext_mask_3d(dif3d)
    #dif_3d_ext[0:1, :, :] = 0
    #dif_3d_ext[(n_frm - 1):, :, :] = 0

    x_from_lst, x_to_lst, y_from_lst, y_to_lst, z_from_lst, z_to_lst = find_bound_3d(dif_3d_ext)

    #print "x_from,   x_to,   y_from,    y_to,  z_from,    z_to "
    #print "_________________________________________________________"
    #for pos in range(len(x_from_lst)):
    #    print x_from_lst[pos], ',    ', x_to_lst[pos], ',   ', y_from_lst[pos], ',   ', y_to_lst[pos], ',   ', z_from_lst[pos], ',   ', z_to_lst[pos]

    return x_from_lst, x_to_lst, y_from_lst, y_to_lst, z_from_lst, z_to_lst

def _create_reflection_list(x_from_lst, x_to_lst, y_from_lst, y_to_lst, z_from_lst, z_to_lst):

    '''Create a reflection list from the spot data.
    
    Params:
        coords The pixel coordinates
        values The pixel values
        spots The pixel->spot mapping
        bbox The spot bounding boxes
        cpos The centroid position
        cvar The centroid variance
        index The list of valid indices
    
    Returns:
        A list of reflections
    '''
    from dials.model.data import Reflection, ReflectionList
    from dials.algorithms.integration import allocate_reflection_profiles

    # Create the reflection list
    length = len(x_from_lst)

    reflection_list = ReflectionList(length)

    for i, r in enumerate(reflection_list):
        bbox = [x_from_lst[i], x_to_lst[i], y_from_lst[i], y_to_lst[i], z_from_lst[i], z_to_lst[i]]
        r.bounding_box = bbox

    #from dials.algorithms.centroid.toy_centroid_Lui import toy_centroid_lui
    #centroid = toy_centroid_lui(reflection_list)
    #reflection_list = centroid.get_reflections()
    return reflection_list
