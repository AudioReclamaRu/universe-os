import unittest
from fractions import Fraction
from buckingham_pi import Dimension, Variable, analyze, paired

def v(name,dims,value=None):
    return Variable(name,Dimension.from_mapping(dims),value=value)

def matrix_rank(matrix):
    a=[[Fraction(x) for x in row] for row in matrix]
    rows,cols=len(a),len(a[0]) if a else 0; pivots=[]; r=0
    for c in range(cols):
        p=next((i for i in range(r,rows) if a[i][c]),None)
        if p is None: continue
        a[r],a[p]=a[p],a[r]; k=a[r][c]; a[r]=[x/k for x in a[r]]
        for i in range(rows):
            if i != r and a[i][c]:
                k=a[i][c]; a[i]=[x-k*y for x,y in zip(a[i],a[r])]
        pivots.append(c); r+=1
    return len(pivots)

class BuckinghamPiTests(unittest.TestCase):
    def test_reynolds_group(self):
        variables=[v("density",{"M":1,"L":-3},1000),v("velocity",{"L":1,"T":-1},2),
                   v("length",{"L":1},.5),v("dynamic_viscosity",{"M":1,"L":-1,"T":-1},.001)]
        result=analyze(variables); self.assertEqual((result.rank,result.nullity),(3,1))
        self.assertEqual(result.canonical_basis[0].exponents,(Fraction(1),Fraction(1),Fraction(1),Fraction(-1)))
        self.assertAlmostEqual(result.canonical_basis[0].numeric_value(variables),1_000_000)
    def test_pendulum_group(self):
        variables=[v("period",{"T":1}),v("length",{"L":1}),v("mass",{"M":1}),v("gravity",{"L":1,"T":-2})]
        result=analyze(variables); self.assertEqual(result.nullity,1)
        self.assertEqual(result.canonical_basis[0].exponents,(Fraction(2),Fraction(-1),Fraction(0),Fraction(1)))
    def test_rank_and_nullity(self):
        variables=[v("length",{"L":1}),v("time",{"T":1}),v("speed",{"L":1,"T":-1}),v("mass",{"M":1})]
        result=analyze(variables); self.assertEqual((result.rank,result.nullity),(3,1))
    def test_dimensionless_inputs(self):
        result=analyze([v("angle",{}),v("phase",{})]); self.assertEqual((result.rank,result.nullity),(0,2))
    def test_alternative_bases_are_complete_and_independent(self):
        variables=[v("density",{"M":1,"L":-3}),v("velocity",{"L":1,"T":-1}),v("length",{"L":1}),
                   v("viscosity",{"M":1,"L":-1,"T":-1}),v("time",{"T":1})]
        result=analyze(variables); self.assertEqual(result.nullity,2); self.assertTrue(result.alternative_bases)
        for basis in result.alternative_bases:
            self.assertEqual(len(basis),result.nullity)
            for group in basis:
                self.assertTrue(all(sum(a*b for a,b in zip(row,group.exponents))==0 for row in result.matrix))
            cols=[[g.exponents[row] for g in basis] for row in range(len(variables))]
            self.assertEqual(matrix_rank(cols),result.nullity)
    def test_duplicate_names(self):
        with self.assertRaises(ValueError): analyze([v("x",{"L":1}),v("x",{"T":1})])
    def test_unknown_dimension(self):
        with self.assertRaises(ValueError): Dimension.from_mapping({"X":1})
    def test_paired_integer(self):
        self.assertEqual(paired(7),"<111_2|21_3>"); self.assertEqual(paired(8),"<1000_2|22_3>")

if __name__=="__main__": unittest.main(verbosity=2)
