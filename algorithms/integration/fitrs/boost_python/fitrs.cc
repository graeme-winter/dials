/*
 * profile_fitting_reciprocal_space.cc
 *
 *  Copyright (C) 2013 Diamond Light Source
 *
 *  Author: James Parkhurst
 *
 *  This code is distributed under the BSD license, a copy of which is
 *  included in the root directory of this package.
 */
#include <boost/python.hpp>
#include <boost/python/def.hpp>
#include <boost/python/iterator.hpp>
#include <dials/algorithms/integration/fitrs/fit.h>

namespace dials { namespace algorithms { namespace boost_python {

  using namespace boost::python;

  template <typename LearnerType>
  af::versa< typename LearnerType::profile_type::value_type, af::c_grid<3> > reference_learner_data(
      const LearnerType &self,
      std::size_t i,
      std::size_t j) {
    af::const_ref< typename LearnerType::profile_type::value_type, af::c_grid<3> > temp = self.data(i,j);
    af::versa< typename LearnerType::profile_type::value_type, af::c_grid<3> > result(temp.accessor());
    std::copy(temp.begin(), temp.end(), result.begin());
    return result;
  }


  void export_profile_fitting_reciprocal_space()
  {
    class_<Spec>("Spec", no_init)
      .def(init< const Beam&,
                 const Detector&,
                 const Goniometer&,
                 const Scan&,
                 double,
                 double,
                 double >())
      ;
    typedef ReciprocalSpaceProfileFitting::reference_learner_type reference_learner_type;

    class_<reference_learner_type>("ReferenceLearner", no_init)
      .def("get", &reference_learner_type::get)
      .def("data", &reference_learner_data<reference_learner_type>)
      .def("count", &reference_learner_type::count)
      .def("__len__", &reference_learner_type::size)
      .def("single_size", &reference_learner_type::single_size)
      .def("nbad", &reference_learner_type::nbad)
      ;

    class_<ReciprocalSpaceProfileFitting>("ReciprocalSpaceProfileFitting", no_init)
      .def(init< std::size_t, double, bool >())
      .def("add", &ReciprocalSpaceProfileFitting::add)
      .def("execute", &ReciprocalSpaceProfileFitting::execute)
      ;
  }

}}} // namespace = dials::algorithms::boost_python
