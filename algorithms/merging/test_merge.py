from __future__ import absolute_import, division, print_function

import pytest

from cctbx import crystal, miller
from scitbx.array_family import flex

from dials.algorithms.merging.merge import delta_F_mean_over_sig_delta_F_mean


def test_delta_F_mean_over_sig_delta_F_mean():
    """Create anomalous difference data and check the calculated value."""
    ms = miller.build_set(
        crystal_symmetry=crystal.symmetry(
            space_group_symbol="P222", unit_cell=(6, 6, 6, 90, 90, 90)
        ),
        anomalous_flag=True,
        d_min=5.0,
    ).expand_to_p1()
    ma = miller.array(
        ms, data=flex.double([1, 2, 1, 3, 1, 4]), sigmas=flex.double(6, 1)
    )
    # differences are (1, 2, 3) i.e. mean 2, sigmas (sqrt2, sqrt2, sqrt2)
    assert delta_F_mean_over_sig_delta_F_mean(ma) == pytest.approx(2 ** 0.5)
