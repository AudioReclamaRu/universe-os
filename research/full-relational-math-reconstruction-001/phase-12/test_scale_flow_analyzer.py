import math
import unittest
from scale_flow_analyzer import analyze_dataset, analyze_payload, paired

class ScaleFlowTests(unittest.TestCase):
    def test_global_power_law_recovers_exponent(self):
        x=[1,2,4,8,16,32]
        y=[v**2 for v in x]
        result=analyze_dataset({"x":x,"y":y})
        self.assertAlmostEqual(result["global_power_law"]["exponent"],2.0)
        self.assertEqual(result["global_power_law"]["atlas_matches_for_exponent"][0]["atlas_key"],"integer.two")

    def test_piecewise_crossover_detected(self):
        x=[1.4**i for i in range(20)]
        xk=1.4**10
        y=[v if v<=xk else v*v/xk for v in x]
        result=analyze_dataset({"x":x,"y":y},min_points_per_regime=5)
        fit=result["two_regime_crossover"]
        self.assertTrue(fit["available"])
        self.assertLess(fit["delta_bic_piecewise_minus_global"],-10)
        self.assertAlmostEqual(fit["exponent_before"],1,places=5)
        self.assertAlmostEqual(fit["exponent_after"],2,places=5)

    def test_crossover_is_not_mislabelled_as_log_periodicity(self):
        x=[1.4**i for i in range(20)]
        xk=1.4**10
        y=[v if v<=xk else v*v/xk for v in x]
        result=analyze_dataset({"x":x,"y":y},min_points_per_regime=5,dsi_grid_size=512)
        dsi=result["discrete_scale_invariance_candidate"]
        self.assertEqual(dsi["trend_baseline"],"two_regime_crossover")
        self.assertEqual(dsi["candidate_status"],"not_supported_against_best_nonperiodic_trend")
        self.assertEqual(dsi["atlas_matches_for_scale_factor"],[])

    def test_log_periodic_scale_factor_recovered(self):
        lam=1.7
        x=[math.exp(0.05*i) for i in range(50)]
        y=[v**1.2*math.exp(0.18*math.cos(2*math.pi*math.log(v)/math.log(lam))) for v in x]
        result=analyze_dataset({"x":x,"y":y},dsi_grid_size=4096)
        dsi=result["discrete_scale_invariance_candidate"]
        self.assertTrue(dsi["available"])
        self.assertEqual(dsi["candidate_status"],"supported_exploratory_candidate")
        self.assertAlmostEqual(dsi["discrete_scale_factor_candidate"],lam,delta=0.025)

    def test_weighted_fit_uses_log_uncertainty(self):
        x=[1,2,3,4,5]
        y=[v**1.5 for v in x]
        result=analyze_dataset({"x":x,"y":y,"sigma_log_y":[.1,.1,.1,.1,.1]})
        self.assertAlmostEqual(result["global_power_law"]["exponent"],1.5)

    def test_duplicate_x_rejected(self):
        with self.assertRaises(ValueError): analyze_dataset({"x":[1,2,2,4],"y":[1,2,3,4]})

    def test_nonpositive_data_rejected(self):
        with self.assertRaises(ValueError): analyze_dataset({"x":[1,2,3,4],"y":[1,2,0,4]})

    def test_sigma_shape_rejected(self):
        with self.assertRaises(ValueError): analyze_dataset({"x":[1,2,3,4],"y":[1,2,3,4],"sigma_log_y":[.1,.1]})

    def test_minimum_regime_size(self):
        with self.assertRaises(ValueError): analyze_dataset({"x":[1,2,3,4],"y":[1,2,3,4]},min_points_per_regime=2)

    def test_payload_requires_dataset(self):
        with self.assertRaises(ValueError): analyze_payload({"datasets":[]})

    def test_paired_count(self):
        self.assertEqual(paired(7),"<111_2|21_3>")

if __name__=="__main__": unittest.main(verbosity=2)
