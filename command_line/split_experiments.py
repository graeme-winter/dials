from __future__ import absolute_import, division, print_function

import functools

from dx2.model.experiment_list import ExperimentList
from libtbx.phil import parse

import dials.util
from dials.array_family import flex
from dials.util import Sorry
from dials.util.export_mtz import match_wavelengths
from dials.util.options import OptionParser, reflections_and_experiments_from_files

help_message = """

Utility script to split experiments and reflections from single files into
multiple files with one experiment per output experiment file and one
reflection file per output experiment file. Alternative options include
splitting by unique detector model or splitting by wavelength. The data
can also be split into chunks rather than individual output files if
required.

Example::

  dials.split_experiments combined.expt combined.refl
"""


class Script(object):
    def __init__(self):
        """Initialise the script."""
        # The phil scope
        phil_scope = parse(
            """
      by_detector = False
        .type = bool
        .help = "If True, instead of producing separate files for each"
                "experiment, experiments are grouped by unique detector"
                "model in the input set of experiments. For example, if"
                "there are five detector models in the input data, five"
                "sets of files will be produced, each containing"
                "experiments that reference a single detector model."
      by_wavelength = False
        .type = bool
        .help = "If True, group experiments by wavelength, from low to high"
                "(using a relative tolerance of 1e-4 to match wavelengths)."
      output {
        experiments_prefix = split
          .type = str
          .help = "Filename prefix for the split experimental models"

        reflections_prefix = split
          .type = str
          .help = "Filename prefix for the split reflections"

        template = "{prefix}_{index:0{maxindexlength:d}d}.{extension}"
          .type = str
          .expert_level = 2
          .help = "Template python format string for output filenames."
                  "Replaced variables are prefix (with"
                  "output.{experiments_prefix, reflections_prefix}),"
                  "index (number of split experiment), maxindexlength"
                  "(number of digits of total number of split experiments)"
                  "and extension (default file extension for model and"
                  "reflection files)"

        chunk_size = None
          .type = int
          .expert_level = 2
          .help = "If not None, instead of creating many individual"
                  "files, create composite files with no more than"
                  "chunk_size experiments per file."
        chunk_sizes = None
          .type = ints
          .expert_level = 2
          .help = "If not None, instead of creating many individual"
                  "files, create composite files with the number of"
                  "datasets given in the chunk_sizes list."

      }
    """,
            process_includes=True,
        )

        # The script usage
        usage = (
            "usage: dials.split_experiments [options] [param.phil] "
            "experiments1.expt experiments2.expt reflections1.refl "
            "reflections2.refl..."
        )

        # Create the parser
        self.parser = OptionParser(
            usage=usage,
            phil=phil_scope,
            read_reflections=True,
            read_experiments=True,
            check_format=False,
            epilog=help_message,
        )

    def run(self, args=None):
        """Execute the script."""

        # Parse the command line
        params, _ = self.parser.parse_args(args, show_diff_phil=True)

        # Try to load the models and data
        if not params.input.experiments:
            print("No Experiments found in the input")
            self.parser.print_help()
            return
        if params.input.reflections:
            if len(params.input.reflections) != len(params.input.experiments):
                raise Sorry(
                    "The number of input reflections files does not match the "
                    "number of input experiments"
                )
        reflections, experiments = reflections_and_experiments_from_files(
            params.input.reflections, params.input.experiments
        )
        if reflections:
            reflections = reflections[0]
        else:
            reflections = None

        experiments_template = functools.partial(
            params.output.template.format,
            prefix=params.output.experiments_prefix,
            maxindexlength=len(str(len(experiments) - 1)),
            extension="expt",
        )

        reflections_template = functools.partial(
            params.output.template.format,
            prefix=params.output.reflections_prefix,
            maxindexlength=len(str(len(experiments) - 1)),
            extension="refl",
        )

        if params.output.chunk_sizes:
            if not sum(params.output.chunk_sizes) == len(experiments):
                raise Sorry(
                    "Sum of chunk sizes list (%s) not equal to number of experiments (%s)"
                    % (sum(params.output.chunk_sizes), len(experiments))
                )

        if params.by_wavelength:
            if reflections:
                if not reflections.experiment_identifiers():
                    raise Sorry(
                        "Unable to split by wavelength as no experiment "
                        "identifiers are set in the reflection table."
                    )
            if all(experiments.identifiers() == ""):
                raise Sorry(
                    "Unable to split by wavelength as no experiment "
                    "identifiers are set in the experiment list."
                )

            wavelengths = match_wavelengths(experiments)
            for i, wl in enumerate(sorted(wavelengths.keys())):
                expids = []
                new_exps = ExperimentList()
                exp_nos = wavelengths[wl]
                for j in exp_nos:
                    expids.append(experiments[j].identifier)  # string
                    new_exps.append(experiments[j])

                experiment_filename = experiments_template(index=i)
                print(
                    "Saving experiments with wavelength %s to %s"
                    % (wl, experiment_filename)
                )
                new_exps.as_json(experiment_filename)
                if reflections:
                    refls = reflections.select_on_experiment_identifiers(expids)
                    reflections_filename = reflections_template(index=i)
                    print(
                        "Saving reflections with wavelength %s to %s"
                        % (wl, reflections_filename)
                    )
                    refls.as_file(reflections_filename)

        elif params.by_detector:
            assert (
                not params.output.chunk_size
            ), "chunk_size + by_detector is not implemented"
            if reflections is None:
                split_data = {
                    detector: {"experiments": ExperimentList()}
                    for detector in experiments.detectors()
                }
            else:
                split_data = {
                    detector: {
                        "experiments": ExperimentList(),
                        "reflections": flex.reflection_table(),
                    }
                    for detector in experiments.detectors()
                }

            for i, experiment in enumerate(experiments):
                split_expt_id = experiments.detectors().index(experiment.detector)
                experiment_filename = experiments_template(index=split_expt_id)
                print("Adding experiment %d to %s" % (i, experiment_filename))
                split_data[experiment.detector]["experiments"].append(experiment)
                if reflections is not None:
                    reflections_filename = reflections_template(index=split_expt_id)
                    print(
                        "Adding reflections for experiment %d to %s"
                        % (i, reflections_filename)
                    )
                    if reflections.experiment_identifiers().keys():
                        # first find which id value corresponds to experiment in question
                        identifier = experiment.identifier
                        id_ = None
                        for k in reflections.experiment_identifiers().keys():
                            if reflections.experiment_identifiers()[k] == identifier:
                                id_ = k
                                break
                        if id_ is None:
                            raise Sorry(
                                "Unable to find id matching experiment identifier in reflection table."
                            )
                        ref_sel = reflections.select(reflections["id"] == id_)
                        # now reset ids and reset/update identifiers map
                        for k in ref_sel.experiment_identifiers().keys():
                            del ref_sel.experiment_identifiers()[k]
                        new_id = len(split_data[experiment.detector]["experiments"]) - 1
                        ref_sel["id"] = flex.int(len(ref_sel), new_id)
                        ref_sel.experiment_identifiers()[new_id] = identifier
                    else:
                        ref_sel = reflections.select(reflections["id"] == i)
                        ref_sel["id"] = flex.int(
                            len(ref_sel),
                            len(split_data[experiment.detector]["experiments"]) - 1,
                        )
                    split_data[experiment.detector]["reflections"].extend(ref_sel)

            for i, detector in enumerate(experiments.detectors()):
                experiment_filename = experiments_template(index=i)
                print("Saving experiment %d to %s" % (i, experiment_filename))
                split_data[detector]["experiments"].as_json(experiment_filename)

                if reflections is not None:
                    reflections_filename = reflections_template(index=i)
                    print(
                        "Saving reflections for experiment %d to %s"
                        % (i, reflections_filename)
                    )
                    split_data[detector]["reflections"].as_file(reflections_filename)
        elif params.output.chunk_size or params.output.chunk_sizes:

            def save_chunk(chunk_id, expts, refls):
                experiment_filename = experiments_template(index=chunk_id)
                print("Saving chunk %d to %s" % (chunk_id, experiment_filename))
                expts.as_json(experiment_filename)
                if refls is not None:
                    reflections_filename = reflections_template(index=chunk_id)
                    print(
                        "Saving reflections for chunk %d to %s"
                        % (chunk_id, reflections_filename)
                    )
                    refls.as_file(reflections_filename)

            chunk_counter = 0
            chunk_expts = ExperimentList()
            if reflections:
                chunk_refls = flex.reflection_table()
            else:
                chunk_refls = None
            for i, experiment in enumerate(experiments):
                chunk_expts.append(experiment)
                if reflections:
                    if reflections.experiment_identifiers().keys():
                        # first find which id value corresponds to experiment in question
                        identifier = experiment.identifier
                        id_ = None
                        for k in reflections.experiment_identifiers().keys():
                            if reflections.experiment_identifiers()[k] == identifier:
                                id_ = k
                                break
                        if id_ is None:
                            raise Sorry(
                                "Unable to find id matching experiment identifier in reflection table."
                            )
                        ref_sel = reflections.select(reflections["id"] == id_)
                        # now reset ids and reset/update identifiers map
                        for k in ref_sel.experiment_identifiers().keys():
                            del ref_sel.experiment_identifiers()[k]
                        new_id = len(chunk_expts) - 1
                        ref_sel["id"] = flex.int(len(ref_sel), new_id)
                        ref_sel.experiment_identifiers()[new_id] = identifier
                    else:
                        ref_sel = reflections.select(reflections["id"] == i)
                        ref_sel["id"] = flex.int(len(ref_sel), len(chunk_expts) - 1)
                    chunk_refls.extend(ref_sel)
                if params.output.chunk_sizes:
                    chunk_limit = params.output.chunk_sizes[chunk_counter]
                else:
                    chunk_limit = params.output.chunk_size
                if len(chunk_expts) == chunk_limit:
                    save_chunk(chunk_counter, chunk_expts, chunk_refls)
                    chunk_counter += 1
                    chunk_expts = ExperimentList()
                    if reflections:
                        chunk_refls = flex.reflection_table()
                    else:
                        chunk_refls = None
            if len(chunk_expts) > 0:
                save_chunk(chunk_counter, chunk_expts, chunk_refls)
        else:
            for i, experiment in enumerate(experiments):

                experiment_filename = experiments_template(index=i)
                print("Saving experiment %d to %s" % (i, experiment_filename))
                ExperimentList([experiment]).as_json(experiment_filename)

                if reflections is not None:
                    reflections_filename = reflections_template(index=i)
                    print(
                        "Saving reflections for experiment %d to %s"
                        % (i, reflections_filename)
                    )
                    ref_sel = reflections.select(reflections["id"] == i)
                    if ref_sel.experiment_identifiers().keys():
                        identifier = ref_sel.experiment_identifiers()[i]
                        for k in ref_sel.experiment_identifiers().keys():
                            del ref_sel.experiment_identifiers()[k]
                        ref_sel["id"] = flex.int(ref_sel.size(), 0)
                        ref_sel.experiment_identifiers()[0] = identifier
                    else:
                        ref_sel["id"] = flex.int(len(ref_sel), 0)
                    ref_sel.as_file(reflections_filename)

        return


@dials.util.show_mail_handle_errors()
def run(args=None):
    script = Script()
    script.run(args)


if __name__ == "__main__":
    run()
