import math
import unittest
from space_time_scaling import analyze_dataset, analyze_payload, paired

class SpaceTimeScalingTests(unittest.TestCase):
    def test_exact_dynamic_exponent(self):
        length=[1,2,4,8,16,32]
        duration=[v**1.5 for v in length]
        result=analyze_dataset({"length":length,"time":duration})
        self.assertAlmostEqual(result["dynamic_scaling_exponent_z"],1.5,places=10)

    def test_unit_rescaling_does_not_change_exponent(self):
        length=[1,2,4,8,16]
        duration=[v**2.0 for v in length]
        first=analyze_dataset({"length":length,"time":duration})
        second=analyze_dataset({"length":[v*1000 for v in length],"time":[v/60 for v in duration]})
        self.assertAlmostEqual(first["dynamic_scaling_exponent_z"],second["dynamic_scaling_exponent_z"],places=10)

    def test_effective_variance_errors_in_variables(self):
        length=[1,2,4,8,16,32,64]
        duration=[v**1.25 * math.exp(e) for v,e in zip(length,[.01,-.02,.015,-.01,.005,.02,-.015])]
        data={"length":length,"time":duration,"sigma_log_length":[.01]*len(length),
              "sigma_log_time":[.02]*len(length),"rho_log_length_time":[.3]*len(length)}
        result=analyze_dataset(data)
        self.assertTrue(result["converged"])
        self.assertEqual(result["fit_method"],"iterative_effective_variance_errors_in_variables")
        self.assertAlmostEqual(result["dynamic_scaling_exponent_z"],1.25,delta=.03)

    def test_time_only_weights(self):
        length=[1,2,4,8,16]
        duration=[v**2 for v in length]
        result=analyze_dataset({"length":length,"time":duration,"sigma_log_time":[.01]*5})
        self.assertAlmostEqual(result["dynamic_scaling_exponent_z"],2,places=10)
        self.assertEqual(result["fit_method"],"weighted_least_squares_time_uncertainty")

    def test_repeated_lengths_allowed(self):
        result=analyze_dataset({"length":[1,2,2,4,8],"time":[1,2,2.1,4,8]})
        self.assertTrue(math.isfinite(result["dynamic_scaling_exponent_z"]))

    def test_requires_explicit_pairs(self):
        with self.assertRaises(ValueError): analyze_payload({"datasets":[{"x":[1,2,3],"y":[1,2,3]}]})

    def test_reject_nonpositive_data(self):
        with self.assertRaises(ValueError): analyze_dataset({"length":[1,2,3],"time":[1,0,3]})

    def test_reject_mismatched_arrays(self):
        with self.assertRaises(ValueError): analyze_dataset({"length":[1,2,3],"time":[1,2]})

    def test_covariance_requirements(self):
        with self.assertRaises(ValueError): analyze_dataset({"length":[1,2,3],"time":[1,2,3],"sigma_log_length":[.1]*3})
        with self.assertRaises(ValueError): analyze_dataset({"length":[1,2,3],"time":[1,2,3],"rho_log_length_time":[.1]*3})

    def test_reject_invalid_correlation(self):
        with self.assertRaises(ValueError): analyze_dataset({"length":[1,2,3],"time":[1,2,3],"sigma_log_length":[.1]*3,"sigma_log_time":[.1]*3,"rho_log_length_time":[0,1.2,0]})

    def test_atlas_comparison_for_z(self):
        result=analyze_dataset({"length":[1,2,4,8],"time":[1,4,16,64]})
        self.assertEqual(result["atlas_matches_for_dynamic_exponent"][0]["atlas_key"],"integer.two")

    def test_paired_count(self):
        self.assertEqual(paired(7),"<111_2|21_3>")

if __name__=="__main__": unittest.main(verbosity=2)
