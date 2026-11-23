import math
import unittest
from uncertainty_propagation import propagate, validate_log_covariance

def fixtures():
    phi=(1+math.sqrt(5))/2
    phase09={"input_provenance":[{"name":"A"},{"name":"B"}],
      "canonical_basis":[{"basis_id":"A","exponents":{"A":"1"}},
                          {"basis_id":"B","exponents":{"B":"1"}}],
      "alternative_basis_examples":[
        {"basis_id":"<1_2|1_3>","groups":[{"basis_id":"A","exponents":{"A":"1","B":"1"}},
                                              {"basis_id":"B","exponents":{"B":"1"}}]},
        {"basis_id":"<10_2|2_3>","groups":[{"basis_id":"A","exponents":{"A":"1","B":"-1"}},
                                               {"basis_id":"B","exponents":{"B":"1"}}]},
        {"basis_id":"<11_2|10_3>","groups":[{"basis_id":"A","exponents":{"A":"1"}},
                                                {"basis_id":"B","exponents":{"A":"1","B":"1"}}]},
        {"basis_id":"<100_2|11_3>","groups":[{"basis_id":"A","exponents":{"A":"1"}},
                                                 {"basis_id":"B","exponents":{"A":"1","B":"-1"}}]}]}
    entries=[("canonical","canonical","GA * GB",{"GA":1,"GB":1}),
             ("alternative","<1_2|1_3>","GA",{"GA":1}),
             ("alternative","<10_2|2_3>","GA * GB^2",{"GA":1,"GB":2}),
             ("alternative","<11_2|10_3>","GB",{"GB":1}),
             ("alternative","<100_2|11_3>","GA^2 * GB^-1",{"GA":2,"GB":-1})]
    phase10={"basis_results":[{"basis_type":typ,"basis_id":bid,"candidate_count":"<1_2|1_3>",
      "candidates":[{"candidate_id":"<1_2|1_3>","formula":formula,"exponent_vector":vector,
                      "value_numeric_secondary":phi,"numeric_evaluation_status":"evaluated_finite_float",
                      "matches":[{"symbol":"φ"}]}]} for typ,bid,formula,vector in entries]}
    cov={"variable_order":["A","B"],"log_relative_covariance":[[0.0001,0.00005],[0.00005,0.0004]],
         "source":"synthetic covariance","status":"idealized"}
    return phase09,phase10,cov

class UncertaintyPropagationTests(unittest.TestCase):
    def test_same_relation_uncertainty_basis_invariant(self):
        p9,p10,cov=fixtures(); result=propagate(p9,p10,cov)
        family=next(f for f in result["basis_invariant_relation_families"] if f["basis_invariant_relation_signature"]=="A * B")
        self.assertEqual(family["representation_count"],"<101_2|12_3>")
        self.assertEqual(family["original_variable_exponents"],{"A":"1","B":"1"})
        self.assertAlmostEqual(family["log_variance"],0.0006)
        self.assertAlmostEqual(family["log_standard_uncertainty"],math.sqrt(0.0006))

    def test_covariance_reorders_by_variable_names(self):
        matrix=validate_log_covariance(["B","A"],[[0.4,0.05],[0.05,0.1]],["A","B"])
        self.assertEqual(matrix,((0.1,0.05),(0.05,0.4)))

    def test_reject_asymmetric_covariance(self):
        with self.assertRaises(ValueError): validate_log_covariance(["A","B"],[[1,0.2],[0.1,1]],["A","B"])

    def test_reject_non_psd_covariance(self):
        with self.assertRaises(ValueError): validate_log_covariance(["A","B"],[[1,2],[2,1]],["A","B"])

    def test_reject_negative_diagonal(self):
        with self.assertRaises(ValueError): validate_log_covariance(["A"],[[-0.1]],["A"])

    def test_reject_variable_order_mismatch(self):
        with self.assertRaises(ValueError): validate_log_covariance(["A","C"],[[1,0],[0,1]],["A","B"])

    def test_unknown_pi_group_is_rejected(self):
        p9,p10,cov=fixtures(); p10["basis_results"][0]["candidates"][0]["exponent_vector"]={"UNKNOWN":1}
        with self.assertRaises(ValueError): propagate(p9,p10,cov)

    def test_exact_fraction_exponents(self):
        p9,p10,cov=fixtures(); p10["basis_results"][0]["candidates"][0]["exponent_vector"]={"GA":"1/2","GB":"1/2"}
        result=propagate(p9,p10,cov)
        self.assertEqual(result["basis_results"][0]["candidates"][0]["original_variable_exponents"],{"A":"1/2","B":"1/2"})

    def test_zero_variance_has_unit_interval(self):
        p9,p10,cov=fixtures(); cov["log_relative_covariance"]=[[0,0],[0,0]]
        result=propagate(p9,p10,cov)
        family=next(f for f in result["basis_invariant_relation_families"] if f["basis_invariant_relation_signature"]=="A * B")
        self.assertEqual(family["multiplicative_log_sigma_interval"],[1.0,1.0])

    def test_singular_positive_semidefinite_covariance_is_allowed(self):
        matrix=validate_log_covariance(["A","B"],[[1,1],[1,1]],["A","B"])
        self.assertEqual(matrix,((1.0,1.0),(1.0,1.0)))

    def test_invalid_covariance_shape(self):
        with self.assertRaises(ValueError): validate_log_covariance(["A","B"],[[1,0]],["A","B"])

if __name__=="__main__": unittest.main(verbosity=2)
