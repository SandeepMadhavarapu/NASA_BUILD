import unittest
import numpy as np
from r4_truss_fem import solve,mast
from r4_terrain import horizon,visibility
class AdvancedTests(unittest.TestCase):
    def test_single_bar(self):
        u,s,res=solve([(0,0,0),(2,0,0)],[(0,1)],[0,1,2,4,5],[[0,0,0],[100,0,0]],200e9,.001)
        self.assertAlmostEqual(u[1,0],1e-6)
        self.assertAlmostEqual(s[0],100000)
        self.assertLess(res,1e-6)
    def test_mast_equilibrium(self):
        r=mast();self.assertLess(r["free_dof_residual_n"],1e-5)
    def test_flat_horizon(self):
        h=horizon(np.zeros((101,101)),50,50,20,mast_m=0,bins=36)
        self.assertTrue(visibility(h,[0,180],[1,1]).all())
        self.assertFalse(visibility(h,[0,180],[-1,-1]).any())
if __name__=="__main__":unittest.main()
