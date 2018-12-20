

#Processes - each cycle of scaling should do scaling and call \
# scaler.expand_scales_to_all_reflections


def expand_and_do_outlier_rejection(scaler, calc_cov=False):
  scaler.expand_scales_to_all_reflections(calc_cov=calc_cov)
  if scaler.params.scaling_options.outlier_rejection:
    # Note just call the method, not the 'outlier_rejection_routine'
    scaler.round_of_outlier_rejection()

def do_intensity_combination(scaler, reselect=True):
  """Do prf/sum intensity combination, optionally reselecting reflections to
  prepare for another minimisation round."""
  if scaler.params.reflection_selection.intensity_choice == 'combine':
    scaler.combine_intensities()
    if scaler.params.scaling_options.outlier_rejection:
      scaler.round_of_outlier_rejection()
  if reselect:
    scaler.make_ready_for_scaling()

def do_error_analysis(scaler, reselect=True, apply_to_reflection_table=False):
  """Do error analysis, optionally reselecting reflections to
  prepare for another minimisation round."""
  if scaler.params.weighting.optimise_errors:
    error_model = scaler.perform_error_optimisation(
      apply_to_reflection_table=apply_to_reflection_table)
  if reselect:
    scaler.make_ready_for_scaling()


def scaling_algorithm(scaler):
  """Main algorithm for scaling"""
  scaler.perform_scaling()

  if scaler.params.reflection_selection.intensity_choice == 'combine' or \
    scaler.params.scaling_options.outlier_rejection:

    expand_and_do_outlier_rejection(scaler)

    do_intensity_combination(scaler, reselect=True)

    scaler.perform_scaling()

  if scaler.params.weighting.optimise_errors or \
    scaler.params.scaling_options.outlier_rejection:

    expand_and_do_outlier_rejection(scaler)

    do_error_analysis(scaler, reselect=True)

    scaler.perform_scaling()

  if scaler.params.scaling_options.full_matrix and \
    scaler.params.scaling_refinery.engine == 'SimpleLBFGS':

    scaler.perform_scaling(engine=scaler.params.scaling_refinery.full_matrix_engine,
      max_iterations=scaler.params.scaling_refinery.full_matrix_max_iterations)

  # The minimisation has only been done on a subset on the data, so apply the
  # scale factors to the whole reflection table.

  scaler.clear_Ih_table()
  expand_and_do_outlier_rejection(scaler, calc_cov=True)
  do_error_analysis(scaler, reselect=False, apply_to_reflection_table=True)

  scaler.adjust_variances()
  scaler.set_outliers()
  scaler.clean_reflection_tables()
  return scaler

def targeted_scaling_algorithm(scaler):
  #Do some rounds of targeted scaling and then exit the algorithm.

  if scaler.params.scaling_options.outlier_rejection:
    expand_and_do_outlier_rejection(scaler)
    scaler.perform_scaling()

  if scaler.params.scaling_options.full_matrix and (
    scaler.params.scaling_refinery.engine == 'SimpleLBFGS'):
    scaler.perform_scaling(
      engine=scaler.params.scaling_refinery.full_matrix_engine,
      max_iterations=scaler.params.scaling_refinery.full_matrix_max_iterations)

  expand_and_do_outlier_rejection(scaler, calc_cov=True)
  #do_error_analysis(scaler, reselect=False)

  scaler.adjust_variances()
  scaler.set_outliers()
  scaler.clean_reflection_tables()
  return scaler
