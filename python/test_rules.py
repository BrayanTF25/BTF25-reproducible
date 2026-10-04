"""Executable tests of exceptional inputs, strict boundaries and deterministic ties."""
import unittest
import numpy as np
import pandas as pd
from btf25 import *
class Rules(unittest.TestCase):
 def test_constant_features(self):
  with self.assertRaises(ValueError):robust_fit(np.ones((10,6)))
 def test_partial_constant(self):
  m=robust_fit(np.c_[np.arange(10),np.ones(10)]);self.assertEqual(m['active'],[True,False])
 def test_iqr_fallback(self):
  m=robust_fit(np.array([[0],[0],[0],[0],[1],[2],[3]]));self.assertGreater(m['scale'][0],0)
 def test_strict_threshold_and_tie(self):
  norm={'median':[0]*6,'scale':[1]*6,'active':[True]*6};m={'binary_normalization':norm,'multiclass_normalization':norm,'threshold_a':2.,'p95_v':1.,'p99_v':2.,'prototypes':[[0]*6]*4}
  f=pd.DataFrame([[2.,0,0,0,0,0,1.],[3.,0,0,0,0,0,2.],[3.,0,0,0,0,0,2.1]],columns=[*[f'r{i}' for i in range(6)],'v_rms']);p=predict(f,m)
  self.assertEqual(p.pred_a.tolist(),[0,1,1]);self.assertEqual(p.pred_b.tolist(),[0,1,1]);self.assertEqual(p.pred_multiclass.tolist(),[0,1,1]);self.assertEqual(p.velocity_level.tolist(),[1,2,3])
 def test_missing_class(self):
  f=pd.DataFrame({'class_id':[0]*10,'block':[1]*10,'v_rms':np.arange(10),**{f'r{i}':np.arange(10) for i in range(6)}})
  with self.assertRaises(ValueError):fit_model(f)
 def test_shapes(self):
  for x in [np.ones((500,2)),np.full((500,3),np.inf)]:
   with self.assertRaises(ValueError):features(x)
 def test_dc(self):self.assertEqual(features(np.ones((500,3)))['v_rms'],0.)
 def test_no_predicted_fault(self):
  m=metrics([0,1],[0,0]);self.assertIsNone(m['precision_fault']);self.assertEqual(m['fn_over_fp'],'infinity')
if __name__=='__main__':unittest.main()
