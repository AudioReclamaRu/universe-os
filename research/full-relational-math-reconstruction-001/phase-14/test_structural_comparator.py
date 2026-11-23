import unittest
from structural_comparator import compare_graph, compare_recurrence, infer_recurrence, analyze_payload

class StructuralComparatorTests(unittest.TestCase):
    def test_q3_reference_exact_isomorphism(self):
        nodes=list(range(8)); edges=[]
        for u in nodes:
            for bit in range(3):
                v=u^(1<<bit)
                if u<v: edges.append([u,v])
        result=compare_graph({"name":"cube3","nodes":nodes,"edges":edges})
        match=next(m for m in result["structural_matches"] if m["reference"]=="Q3")
        self.assertTrue(match["exact_isomorphic"])

    def test_relabelled_cycle_exact_isomorphism(self):
        nodes=["a","b","c","d","e"]
        edges=[["a","c"],["c","e"],["e","b"],["b","d"],["d","a"]]
        result=compare_graph({"nodes":nodes,"edges":edges})
        match=next(m for m in result["structural_matches"] if m["reference"]=="C5")
        self.assertTrue(match["exact_isomorphic"])

    def test_graph_spectral_moments_and_cycle_rank(self):
        result=compare_graph({"nodes":[0,1,2,3],"edges":[[0,1],[1,2],[2,3]]})
        self.assertEqual(result["graph"]["cycle_rank"],"<0_2|0_3>")
        self.assertEqual(result["graph"]["diameter"],"<11_2|10_3>")
        self.assertEqual(result["graph"]["bipartite"],True)

    def test_nonisomorphic_spectral_match_not_overstated(self):
        result=compare_graph({"nodes":list(range(6)),"edges":[[i,(i+1)%6] for i in range(6)]})
        match=next(m for m in result["structural_matches"] if m["reference"]=="C6")
        self.assertTrue(match["spectral_fingerprint_equal"])
        self.assertTrue(match["exact_isomorphic"])

    def test_k4_triangle_count(self):
        nodes=list(range(4))
        edges=[[i,j] for i in range(4) for j in range(i+1,4)]
        result=compare_graph({"nodes":nodes,"edges":edges})
        self.assertEqual(result["graph"]["triangle_count"],"<100_2|11_3>")

    def test_spectral_moments_use_paired_integer_notation(self):
        result=compare_graph({"nodes":[0,1],"edges":[[0,1]]})
        self.assertEqual(result["graph"]["adjacency_spectral_moments"][1],"<10_2|2_3>")

    def test_empty_graph_rejected(self):
        with self.assertRaises(ValueError): compare_graph({"nodes":[],"edges":[]})

    def test_reject_duplicate_edges(self):
        with self.assertRaises(ValueError): compare_graph({"nodes":[1,2],"edges":[[1,2],[2,1]]})

    def test_reject_self_loop(self):
        with self.assertRaises(ValueError): compare_graph({"nodes":[1],"edges":[[1,1]]})

    def test_fibonacci_operator_match(self):
        sequence=[0,1,1,2,3,5,8,13,21,34,55,89]
        result=compare_recurrence(sequence)
        self.assertIn("fibonacci_operator",result["operator_matches"])
        self.assertIn("fibonacci_operator",result["exact_initial_state_matches"])

    def test_scaled_fibonacci_projective_state(self):
        sequence=[0,3,3,6,9,15,24,39,63,102]
        result=compare_recurrence(sequence)
        match=next(m for m in result["projective_initial_state_matches"] if m["reference"]=="fibonacci_operator")
        self.assertEqual(match["initial_state_scale_factor"],"<11_2|10_3>")
        self.assertNotIn("fibonacci_operator",result["exact_initial_state_matches"])

    def test_lucas_shares_operator_not_initial_state(self):
        sequence=[2,1,3,4,7,11,18,29,47,76]
        result=compare_recurrence(sequence)
        self.assertIn("fibonacci_operator",result["operator_matches"])
        self.assertIn("lucas_operator",result["exact_initial_state_matches"])

    def test_tribonacci_operator(self):
        sequence=[0,0,1,1,2,4,7,13,24,44,81,149]
        result=compare_recurrence(sequence)
        self.assertIn("tribonacci_operator",result["operator_matches"])

    def test_finite_sequence_no_unique_low_order_recurrence(self):
        result=infer_recurrence([1,4,2,7,3,9,5,12],max_order=3)
        self.assertIsNone(result)

    def test_paired_counts_and_payload(self):
        result=analyze_payload({"sequences":[{"name":"fib","terms":[0,1,1,2,3,5,8,13]}]})
        self.assertEqual(result["sequence_candidate_count"],"<1_2|1_3>")


if __name__=="__main__": unittest.main(verbosity=2)
