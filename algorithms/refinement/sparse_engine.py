from __future__ import division
#
#  Copyright (C) (2016) Lawrence Berkeley National Laboratory
#
#  Author: Nicholas Sauter.
#
#  This code is distributed under the BSD license, a copy of which is
#  included in the root directory of this package.
#
import libtbx
from libtbx.utils import Sorry
from scitbx.array_family import flex
from logging import debug, info
from engine import DisableMPmixin

try:
  from scitbx.examples.bevington import non_linear_ls_eigen_wrapper
except ImportError,e:
  raise Sorry("""Eigen package is not available.  Please untar the Eigen source package
     (http://eigen.tuxfamily.org) and place a link to it (eigen--> Eigen source dir) in
     the modules directory of your developer install; then recompile.
""")

from engine import AdaptLstbx as AdaptLstbxBase

class AdaptLstbxSparse(DisableMPmixin, AdaptLstbxBase, non_linear_ls_eigen_wrapper):
  """Adapt the base class for Eigen"""

  def __init__(self, target, prediction_parameterisation, log=None,
               verbosity = 0, track_step = False, track_gradient = False,
               track_parameter_correlation = False,
               track_out_of_sample_rmsd = False, max_iterations = None):

    AdaptLstbxBase.__init__(self, target, prediction_parameterisation,
             log=log, verbosity=verbosity, track_step=track_step,
             track_gradient=track_gradient,
             track_parameter_correlation=track_parameter_correlation,
             track_out_of_sample_rmsd=track_out_of_sample_rmsd,
             max_iterations=max_iterations)

    non_linear_ls_eigen_wrapper.__init__(self, n_parameters = len(self._parameters))

from engine import GaussNewtonIterations as GaussNewtonIterationsBase
class GaussNewtonIterations(AdaptLstbxSparse, GaussNewtonIterationsBase):
  """Refinery implementation, using lstbx Gauss Newton iterations"""

  def __init__(self, target, prediction_parameterisation, log=None,
               verbosity=0, track_step=False, track_gradient=False,
               track_parameter_correlation=False,
               track_out_of_sample_rmsd=False,
               max_iterations=20, **kwds):

    AdaptLstbxSparse.__init__(self, target, prediction_parameterisation,
             log=log, verbosity=verbosity, track_step=track_step,
             track_gradient=track_gradient,
             track_parameter_correlation=track_parameter_correlation,
             track_out_of_sample_rmsd=track_out_of_sample_rmsd,
             max_iterations=max_iterations)

    # add an attribute to the journal
    self.history.add_column("reduced_chi_squared")#flex.double()

    # adopt any overrides of the defaults above
    libtbx.adopt_optional_init_args(self, kwds)

from engine import LevenbergMarquardtIterations
class SparseLevenbergMarquardtIterations(GaussNewtonIterations,LevenbergMarquardtIterations):
  """Levenberg Marquardt with Sparse matrix algebra"""

  def set_cholesky_factor(self):
    """Override that disables this method of the base AdaptLstbx. For
    sparse, large matrices this is numberically unstable; not to mention it
    is not implemented for the Eigen wrapper"""
    pass

  def setup_mu(self):
    '''Override that works with the Eigen wrapper'''
    a_diag = self.get_normal_matrix_diagonal()
    self.mu = self.tau * flex.max(a_diag)

  def add_constant_to_diagonal(self, mu):
    '''Delegate to the method of non_linear_ls_eigen_wrapper'''
    non_linear_ls_eigen_wrapper.add_constant_to_diagonal(self, self.mu)

  def report_progress(self, objective):
    '''Override for the Eigen wrapper to provide live feedback of progress
    of the refinement'''
    if self._verbosity > 1:
      info("Iteration: %5d Objective: %18.4f Mu: %12.7f" % (self.n_iterations, objective, self.mu))
    else:
      debug("Iteration: %5d Objective: %18.4f Mu: %12.7f" % (self.n_iterations, objective, self.mu))

  def run(self):
    self._run_core()

    # In contrast to dense matrix (traditional) LevMar, sparse matrix assumes
    # that the matrix is extremely large and not easily inverted. Therefore,
    # no attempt here to calculate esd's based on the variance covariance
    # matrix.

    if self._verbosity > 0:
      info(self.get_eigen_summary())
    return
