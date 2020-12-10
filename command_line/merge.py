"""
Command line script to allow merging and truncating of a dials dataset.
"""

import logging
import sys
from io import StringIO

from dx2.model import ExperimentList

from iotbx import phil

from dials.algorithms.merging.merge import (
    MTZDataClass,
    make_merged_mtz_file,
    merge,
    show_wilson_scaling_analysis,
    truncate,
)
from dials.algorithms.scaling.scaling_library import determine_best_unit_cell
from dials.util import Sorry, log, show_mail_handle_errors
from dials.util.export_mtz import match_wavelengths
from dials.util.options import OptionParser, reflections_and_experiments_from_files
from dials.util.version import dials_version

help_message = """
Merge scaled dials data.

Examples::

  dials.merge scaled.expt scaled.refl

  dials.merge scaled.expt scaled.refl truncate=False
"""

logger = logging.getLogger("dials")
phil_scope = phil.parse(
    """
assess_space_group = True
    .type = bool
    .help = "Option to assess space group by testing presence of axial reflections"
anomalous = True
    .type = bool
    .help = "Output anomalous as well as mean intensities."
truncate = True
    .type = bool
    .help = "Option to perform truncation on merged data."
d_min = None
    .type = float
    .help = "High resolution limit to apply to the data."
d_max = None
    .type = float
    .help = "Low resolution limit to apply to the data."
combine_partials = True
    .type = bool
    .help = "Combine partials that have the same partial id into one
        reflection, with an updated partiality given by the sum of the
        individual partialities."
partiality_threshold=0.4
    .type = float
    .help = "All reflections with partiality values above the partiality
        threshold will be retained. This is done after any combination of
        partials if applicable."
best_unit_cell = None
    .type = unit_cell
    .help = "Best unit cell value, to use when performing resolution cutting,"
            "and as the overall unit cell in the merged mtz. If undefined, the median"
            "cell will be used."
n_residues = 200
    .type = int
    .help = "Number of residues to use in Wilson scaling"
merging {
    use_internal_variance = False
        .type = bool
    n_bins = 20
        .type = int(value_min=5)
    anomalous = False
        .type = bool
        .help = "Option to control whether reported merging stats are anomalous."
}
output {
    log = dials.merge.log
        .type = str
    mtz = merged.mtz
        .type = str
        .help = "Filename to use for mtz output."
    crystal_names = XTAL
        .type = strings
        .help = "Crystal name to be used in MTZ file output (multiple names
            allowed for MAD datasets)"
    project_name = AUTOMATIC
        .type = str
        .help = "Project name to be used in MTZ file output"
    dataset_names = NATIVE
        .type = strings
        .help = "Dataset name to be used in MTZ file output (multiple names
            allowed for MAD datasets)"
}
""",
    process_includes=True,
)


def merge_data_to_mtz(params, experiments, reflections):
    """Merge data (at each wavelength) and write to an mtz file object."""
    wavelengths = match_wavelengths(experiments)  # wavelengths is an ordered dict
    mtz_datasets = [
        MTZDataClass(wavelength=w, project_name=params.output.project_name)
        for w in wavelengths.keys()
    ]
    dataset_names = params.output.dataset_names
    crystal_names = params.output.crystal_names

    # check if best_unit_cell is set.
    best_unit_cell = params.best_unit_cell
    if not best_unit_cell:
        best_unit_cell = determine_best_unit_cell(experiments)
    reflections[0]["d"] = best_unit_cell.d(reflections[0]["miller_index"])
    for expt in experiments:
        expt.crystal.unit_cell = best_unit_cell

    if len(wavelengths) > 1:
        logger.info(
            "Multiple wavelengths found: \n%s",
            "\n".join(
                "  Wavlength: %.5f, experiment numbers: %s "
                % (k, ",".join(map(str, v)))
                for k, v in wavelengths.items()
            ),
        )
        if not dataset_names or len(dataset_names) != len(wavelengths):
            logger.info(
                "Unequal number of dataset names and wavelengths, using default naming."
            )
            dataset_names = [None] * len(wavelengths)
        if not crystal_names or len(crystal_names) != len(wavelengths):
            logger.info(
                "Unequal number of crystal names and wavelengths, using default naming."
            )
            crystal_names = [None] * len(wavelengths)
        experiments_subsets = []
        reflections_subsets = []
        for dataset, dname, cname in zip(mtz_datasets, dataset_names, crystal_names):
            dataset.dataset_name = dname
            dataset.crystal_name = cname
        for exp_nos in wavelengths.values():
            expids = [experiments[i].identifier for i in exp_nos]
            experiments_subsets.append(
                ExperimentList([experiments[i] for i in exp_nos])
            )
            reflections_subsets.append(
                reflections[0].select_on_experiment_identifiers(expids)
            )
    else:
        mtz_datasets[0].dataset_name = dataset_names[0]
        mtz_datasets[0].crystal_name = crystal_names[0]
        experiments_subsets = [experiments]
        reflections_subsets = reflections

    for experimentlist, reflection_table, mtz_dataset in zip(
        experiments_subsets, reflections_subsets, mtz_datasets
    ):
        # merge and truncate the data
        merged_array, merged_anomalous_array, stats_summary = merge(
            experimentlist,
            reflection_table,
            d_min=params.d_min,
            d_max=params.d_max,
            combine_partials=params.combine_partials,
            partiality_threshold=params.partiality_threshold,
            best_unit_cell=best_unit_cell,
            anomalous=params.anomalous,
            assess_space_group=params.assess_space_group,
            n_bins=params.merging.n_bins,
            use_internal_variance=params.merging.use_internal_variance,
        )
        mtz_dataset.merged_array = merged_array
        mtz_dataset.merged_anomalous_array = merged_anomalous_array
        if params.anomalous:
            merged_intensities = merged_anomalous_array
        else:
            merged_intensities = merged_array

        if params.truncate:
            amplitudes, anomalous_amplitudes = truncate(merged_intensities)
            mtz_dataset.amplitudes = amplitudes
            mtz_dataset.anomalous_amplitudes = anomalous_amplitudes
        show_wilson_scaling_analysis(merged_intensities)
        if stats_summary:
            logger.info(stats_summary)

    return make_merged_mtz_file(mtz_datasets)


@show_mail_handle_errors()
def run(args=None):
    """Run the merging from the command-line."""
    usage = """Usage: dials.merge scaled.refl scaled.expt [options]"""

    parser = OptionParser(
        usage=usage,
        read_experiments=True,
        read_reflections=True,
        phil=phil_scope,
        check_format=False,
        epilog=help_message,
    )
    params, options = parser.parse_args(args=args, show_diff_phil=False)

    if not params.input.experiments or not params.input.reflections:
        parser.print_help()
        sys.exit()

    reflections, experiments = reflections_and_experiments_from_files(
        params.input.reflections, params.input.experiments
    )

    log.config(verbosity=options.verbose, logfile=params.output.log)
    logger.info(dials_version())

    diff_phil = parser.diff_phil.as_str()
    if diff_phil != "":
        logger.info("The following parameters have been modified:\n")
        logger.info(diff_phil)

    ### Assert that all data have been scaled with dials - should only be
    # able to input one reflection table and experimentlist that are
    # matching and scaled together.

    if len(reflections) != 1:
        raise Sorry(
            """Only data scaled together as a single reflection dataset
can be processed with dials.merge"""
        )

    for k in [
        "intensity.scale.value",
        "intensity.scale.variance",
        "inverse_scale_factor",
    ]:
        if k not in reflections[0]:
            raise Sorry(
                """%s not found in the reflection table.
Only scaled data can be processed with dials.merge"""
                % k
            )

    try:
        mtz_file = merge_data_to_mtz(params, experiments, reflections)
    except ValueError as e:
        raise Sorry(e)

    logger.info("\nWriting reflections to %s", (params.output.mtz))
    out = StringIO()
    mtz_file.show_summary(out=out)
    logger.info(out.getvalue())
    mtz_file.write(params.output.mtz)


if __name__ == "__main__":
    run()
