from __future__ import division
from libtbx import test_utils
import libtbx.load_env

tst_list = (
    "$D/test/tst_spots_xds.py",
    "$D/test/array_family/tst_flex_shoebox.py",
    "$D/test/model/data/tst_reflection_pickle.py",
    "$D/test/model/data/tst_shoebox.py",
    "$D/test/model/data/tst_prediction.py",
    "$D/test/model/data/tst_observation.py",
    "$D/test/model/experiment/tst_crystal_model.py",
    "$D/test/algorithms/spot_prediction/tst_index_generator.py",
    "$D/test/algorithms/spot_prediction/tst_ray_predictor.py",
    "$D/test/algorithms/spot_prediction/tst_rotation_angles.py",
    "$D/test/algorithms/spot_prediction/tst_spot_prediction.py",
    "$D/test/algorithms/integration/profile/tst_grid_sampler.py",
    "$D/test/algorithms/integration/profile/tst_xds_circle_sampler.py",
    "$D/test/algorithms/integration/profile/tst_reference_locator.py",
    "$D/test/algorithms/integration/profile/tst_reference_learner.py",
    "$D/test/algorithms/integration/profile/tst_profile_fitting.py",
    "$D/test/algorithms/centroid/tst_filtered_centroid.py",
    "$D/test/algorithms/centroid/tst_lui_centroid.py",
    "$D/test/algorithms/centroid/tst_toy_centroid.py",
    "$D/test/algorithms/centroid/tst_toy_centroid_helpers.py",
    "$B/test/algorithms/spatial_indexing/tst_quadtree",
    "$B/test/algorithms/spatial_indexing/tst_octree",
    "$B/test/algorithms/spatial_indexing/tst_collision_detection",
    "$D/test/algorithms/refinement/tst_refinement_regression.py",
    "$D/test/algorithms/refinement/tst_prediction_parameters.py",
    "$D/test/algorithms/refinement/tst_beam_parameters.py",
    "$D/test/algorithms/refinement/tst_crystal_parameters.py",
    "$D/test/algorithms/refinement/tst_detector_parameters.py",
    "$D/test/algorithms/image/tst_centroid.py",
    "$D/test/algorithms/image/filter/tst_summed_area.py",
    "$D/test/algorithms/image/filter/tst_mean_and_variance.py",
    "$D/test/algorithms/image/filter/tst_median.py",
    "$D/test/algorithms/image/filter/tst_fano.py",
    "$D/test/algorithms/image/threshold/tst_local.py",
    "$D/test/algorithms/image/connected_components/tst_connected_components.py",
    "$D/test/algorithms/polygon/clip/tst_clipping.py",
    "$D/test/algorithms/polygon/tst_spatial_interpolation.py",
    "$D/test/algorithms/reflection_basis/tst_coordinate_system.py",
    "$D/test/algorithms/reflection_basis/tst_map_frames.py",
    "$D/test/algorithms/reflection_basis/tst_beam_vector_map.py",
    "$D/test/algorithms/reflection_basis/tst_grid_index_generator.py",
    "$D/test/algorithms/reflection_basis/tst_transform.py",
    "$D/test/algorithms/shoebox/tst_bbox_calculator.py",
    "$D/test/algorithms/shoebox/tst_mask_foreground.py",
    "$D/test/algorithms/shoebox/tst_mask_overlapping.py",
    "$D/test/algorithms/shoebox/tst_extractor.py",
    "$D/test/algorithms/shoebox/tst_helpers.py",
    "$D/test/algorithms/peak_finding/tst_spotfinder.py",
    "$D/scratch/rjg/tst_index.py",
    )

def run () :
    build_dir = libtbx.env.under_build("dials")
    dist_dir = libtbx.env.dist_path("dials")
    test_utils.run_tests(build_dir, dist_dir, tst_list)

if (__name__ == "__main__"):
    run()
