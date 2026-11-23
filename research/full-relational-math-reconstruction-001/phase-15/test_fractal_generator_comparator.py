import math
import unittest
from fractal_generator_comparator import analyze_ifs, analyze_quadratic_dynamics, analyze_payload, reference_ifs

class FractalGeneratorComparatorTests(unittest.TestCase):
    def test_cantor_ifs_exact_match_and_dimension(self):
        result=analyze_ifs(reference_ifs("cantor_set"))
        self.assertIn("cantor_set",result["exact_reference_matches"])
        self.assertAlmostEqual(result["similarity_dimension_numeric_secondary"],math.log(2)/math.log(3))
        self.assertEqual(result["common_similarity_ratio"],"<1_2|1_3>/<11_2|10_3>")

    def test_sierpinski_gasket_affine_barycentric_match(self):
        result=analyze_ifs(reference_ifs("sierpinski_gasket"))
        self.assertIn("sierpinski_gasket",result["exact_reference_matches"])
        self.assertAlmostEqual(result["similarity_dimension_numeric_secondary"],math.log(3)/math.log(2))

    def test_sierpinski_carpet_map_count_and_match(self):
        result=analyze_ifs(reference_ifs("sierpinski_carpet"))
        self.assertIn("sierpinski_carpet",result["exact_reference_matches"])
        self.assertEqual(result["map_count"],"<1000_2|22_3>")

    def test_menger_sponge_map_count_and_match(self):
        result=analyze_ifs(reference_ifs("menger_sponge"))
        self.assertIn("menger_sponge",result["exact_reference_matches"])
        self.assertEqual(result["map_count"],"<10100_2|202_3>")
        self.assertAlmostEqual(result["similarity_dimension_numeric_secondary"],math.log(20)/math.log(3))

    def test_koch_curve_algebraic_rotation_maps(self):
        result=analyze_ifs(reference_ifs("koch_curve"))
        self.assertIn("koch_curve",result["exact_reference_matches"])
        self.assertEqual(result["common_similarity_ratio"],"<1_2|1_3>/<11_2|10_3>")

    def test_map_order_is_irrelevant(self):
        ref=reference_ifs("cantor_set"); ref["maps"]=list(reversed(ref["maps"]))
        self.assertIn("cantor_set",analyze_ifs(ref)["exact_reference_matches"])

    def test_coordinate_system_is_not_silently_ignored(self):
        ref=reference_ifs("sierpinski_gasket"); ref["coordinate_system"]="euclidean_xy"
        self.assertNotIn("sierpinski_gasket",analyze_ifs(ref)["exact_reference_matches"])

    def test_noncontractive_generator_not_certified(self):
        raw={"dimension":1,"maps":[{"matrix":[["1"]],"translation":["0"]}]}
        result=analyze_ifs(raw)
        self.assertFalse(result["contractive_infinity_norm_bound"])
        self.assertIsNone(result["similarity_dimension_numeric_secondary"])

    def test_mandelbrot_parameter_family_match(self):
        result=analyze_quadratic_dynamics({"name":"Mandelbrot","parameter_mode":"variable",
            "coefficients":[0,0,1],"parameter_coefficient":1})
        self.assertIn("mandelbrot_quadratic_parameter_family",result["exact_structural_matches"])
        self.assertEqual(result["normalized_parameter_expression"],"C = <0_2|0_3> + (<1_2|1_3>)*c")

    def test_julia_c_zero_match(self):
        result=analyze_quadratic_dynamics({"name":"Julia zero","parameter_mode":"fixed","coefficients":[0,0,1]})
        self.assertIn("julia_map_c0",result["exact_structural_matches"])
        self.assertEqual(result["fixed_normalized_C"]["real"],"<0_2|0_3>")

    def test_julia_c_minus_one_match(self):
        result=analyze_quadratic_dynamics({"parameter_mode":"fixed","coefficients":[-1,0,1]})
        self.assertIn("julia_map_c_minus1",result["exact_structural_matches"])

    def test_affine_conjugacy_to_normal_form(self):
        result=analyze_quadratic_dynamics({"parameter_mode":"fixed","coefficients":[{"real":"1/2","imag":0},4,2]})
        self.assertEqual(result["fixed_normalized_C"]["real"],"-<1_2|1_3>")
        self.assertIn("julia_map_c_minus1",result["exact_structural_matches"])

    def test_parameter_role_separates_family_from_fixed_map(self):
        family=analyze_quadratic_dynamics({"parameter_mode":"variable","coefficients":[0,0,1]})
        fixed=analyze_quadratic_dynamics({"parameter_mode":"fixed","coefficients":[0,0,1]})
        self.assertIn("mandelbrot_quadratic_parameter_family",family["exact_structural_matches"])
        self.assertNotIn("mandelbrot_quadratic_parameter_family",fixed["exact_structural_matches"])
        self.assertIn("quadratic_julia_fixed_parameter_family",fixed["exact_structural_matches"])

    def test_reject_nonquadratic_or_zero_leading_coefficient(self):
        with self.assertRaises(ValueError): analyze_quadratic_dynamics({"coefficients":[0,1]})
        with self.assertRaises(ValueError): analyze_quadratic_dynamics({"coefficients":[0,1,0]})

    def test_payload_requires_candidate(self):
        with self.assertRaises(ValueError): analyze_payload({})

if __name__=="__main__": unittest.main(verbosity=2)
