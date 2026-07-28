import unittest
import numpy as np
from ref import v24,v244,v244_oracle

class V244Tests(unittest.TestCase):
    def test_compound_statistic_oracle(self):
        obs=v24.generate_world("context_split",799100,length=8)["observations"]
        y,m,c=v244.encode(obs)
        self.assertAlmostEqual(float(v244.batch_statistic(y[None],m[None],c)[0]),
                               v244_oracle.scalar_compound_statistic(obs),places=10)
    def test_randomization_custody(self):
        obs=v24.generate_world("context_split",799101,length=8)["observations"]
        ys,ms,c=v244.randomization_batch(obs,799101,19); y,m,_=v244.encode(obs)
        for cue in range(3):
            idx=np.flatnonzero(c==cue)
            self.assertTrue(all(sorted(row[idx])==sorted(y[idx]) for row in ys))
            self.assertTrue(all(sorted(row[idx])==sorted(m[idx]) for row in ms))
    def test_rank_formula(self):
        values=[-2.,0.,1.,3.,4.,5.,7.]
        self.assertEqual(v244_oracle.rank_pvalue(3.,values),5/8)
        self.assertEqual(v244_oracle.nearest_rank_95(values),7.)
