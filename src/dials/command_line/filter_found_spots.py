import logging

import iotbx.phil
from dxtbx.model.experiment_list import ExperimentList

from dials.array_family import flex
from dials.util import Sorry, log, show_mail_handle_errors
from dials.util.options import ArgumentParser, reflections_and_experiments_from_files

help_message = __doc__

phil_scope = iotbx.phil.parse(
"""\
  minspots = 20
    .type = int(value_min=0)
    .help = "Minimum number of spots per sweep"
    
  maxspots = 100000
    .type = int
    .help = "Maximum number of spots per sweep"
    
  output {
     experiments = 'hits.expt'
        .type = str
        .help = "The filtered experiments output filename"
     reflections = 'hits.refl'
        .type = str
        .help = "The filtered reflections output filename"
     log = 'dials.filter_found_spots.log'
        .type = str
        .help = "Name of log file"
    }
""",
)

logger = logging.getLogger('dials.command_line.index.find_hits')

#@show_mail_handle_errors()
def run(args=None):
    
    usage = 'dials.python find_hits.py imported.expt strong.refl [options]'
    parser = ArgumentParser(
        usage=usage,
        phil=phil_scope,
        read_experiments=True,
        read_reflections=True,
        epilog=help_message,
    )

    params, options, args = parser.parse_args(
        args, show_diff_phil=False, return_unhandled=True
    )
    
    log.config(verbosity=options.verbose, logfile=params.output.log)
    
    # Log the diff phil
    diff_phil = parser.diff_phil.as_str()
    if diff_phil != "":
        logger.info("The following parameters have been modified:\n")
        logger.info(diff_phil)
    
    refl, expt = reflections_and_experiments_from_files(
        params.input.reflections, params.input.experiments
    )
    refl = refl[0] # why is this a list?

    # keep only indexed reflections
    indexed = refl.select(refl.get_flags(refl.flags.indexed))
    if indexed.size() > 0:
        logger.info(f'Keeping indexed reflections only ({indexed.size()} / {refl.size()})')
        refl = indexed
    else:
        logger.info('These are unindexed reflections')

    ids = refl["id"]

    keep_expt = ExperimentList()
    keep_refl = flex.reflection_table()

    for j, e in enumerate(expt):
        nn = (ids == j).count(True)
        if (nn > params.minspots) and (nn < params.maxspots):
            keep = refl.select(ids == j)
            keep["id"] = flex.int(keep.size(), len(keep_expt))
            keep_refl.extend(keep)
            keep_expt.append(e)

    logger.info('-'*80)
    logger.info(f'Found {len(keep_expt)} hits ({len(keep_expt)}/{len(expt)} = {(len(keep_expt)/len(expt)):.1%})')
    logger.info(f'Saving hits to {params.output.experiments}, {params.output.reflections}')
    logger.info('-'*80)
    
    keep_expt.as_file(params.output.experiments)
    keep_refl.as_file(params.output.reflections)
    
if __name__ == "__main__":
    run()