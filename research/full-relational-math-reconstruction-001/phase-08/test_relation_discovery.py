import math
import unittest
from relation_discovery import Dim, Q, Finder, paired

class Tests(unittest.TestCase):
    def test_pair_notation(self):
        self.assertEqual(paired(7), "<111_2|21_3>")
    def test_dimension_arithmetic(self):
        self.assertTrue((Dim.of({"L":1}) / Dim.of({"T":1}) / Dim.of({"L":1}) * Dim.of({"T":1})).dimensionless)
    def test_reject_unlike_dimensions(self):
        self.assertEqual(Finder().discover([Q("l",2,Dim.of({"L":1})),Q("t",1,Dim.of({"T":1}))]),[])
    def test_phi_match(self):
        qs=[Q("one",1,Dim()),Q("candidate",(1+math.sqrt(5))/2,Dim())]
        c=Finder(tolerance=1e-10).discover(qs)[0]
        self.assertEqual(c.matches[0]["key"],"constant.phi")
    def test_cross_ratio_same_frame_only(self):
        qs=[Q(str(x),x,Dim.of({"L":1}),frame="axis") for x in (0,1,2,3)]
        self.assertTrue(any(c.operation=="cross_ratio" and math.isclose(c.value,4/3) for c in Finder().discover(qs,True)))
        other=[Q(str(x),x,Dim.of({"L":1})) for x in (0,1,2,3)]
        self.assertFalse(any(c.operation=="cross_ratio" for c in Finder().discover(other,True)))
    def test_uncertainty(self):
        qs=[Q("a",10,Dim.of({"L":1}),.1),Q("b",5,Dim.of({"L":1}),.2)]
        c=next(x for x in Finder().discover(qs) if x.formula=="(a) / (b)")
        self.assertGreater(c.uncertainty,0)
    def test_duplicate_names(self):
        with self.assertRaises(ValueError): Finder().discover([Q("a",1,Dim()),Q("a",2,Dim())])
    def test_power_exponent(self):
        fit=Finder(tolerance=1e-10).power_law([1,2,4,8],[1,4,16,64])
        self.assertAlmostEqual(fit["exponent"],2); self.assertAlmostEqual(fit["r_squared"],1)
    def test_power_positive_domain(self):
        with self.assertRaises(ValueError): Finder().power_law([1,2,3],[1,0,9])

if __name__=="__main__": unittest.main(verbosity=2)
