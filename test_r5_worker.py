import unittest
from unittest.mock import patch
from r5_engineering import BASE,geometry,thermal,construction
from r5_worker import candidates,compare,convergence,save
from pathlib import Path
import tempfile,json
class WorkerTests(unittest.TestCase):
    def test_queue(self):
        q=candidates();self.assertEqual(len(q),48);self.assertEqual(len({tuple(sorted(x.items())) for x in q}),48)
    def test_geometry(self):
        import math
        for n in (1,4):
            d=BASE|{'modules':n};g=geometry(d)
            self.assertAlmostEqual(math.pi*g['diameter_m']**3/4*2600*n,d['mass'],places=6)
    def test_dark_cold(self):
        r=thermal(BASE,[0]*24,cold=True);self.assertEqual(r['minimum_kw'],0);self.assertAlmostEqual(r['unserved_kwh'],126)
    def test_ledger(self):
        for solid in (True,False):
            r=thermal(BASE|{'solid':solid},[1]*200+[0]*200);self.assertLess(r['residual'],1e-9);self.assertTrue(0<=r['final_usable_fraction']<=1)
    def test_shutter(self):
        timeline=[0]*708
        a=thermal(BASE,timeline,fault={'shutter':True});b=thermal(BASE|{'shutter_backup':True},timeline,fault={'shutter':True})
        self.assertLessEqual(b['unserved_kwh'],a['unserved_kwh'])
    def test_common_failure(self):
        t=[0]*708
        self.assertEqual(thermal(BASE,t,fault={'common_shutter':True}),thermal(BASE|{'shutter_backup':True},t,fault={'common_shutter':True}))
    def test_construction(self):
        self.assertGreater(construction(BASE)['local_material_kg'],BASE['mass'])
        self.assertGreater(construction(BASE|{'modules':4})['local_material_kg'],construction(BASE)['local_material_kg'])
    def test_atomic_save(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'state.json';save(p,{'rows':[1]});self.assertEqual(json.loads(p.read_text()),{'rows':[1]});self.assertFalse(p.with_suffix('.tmp').exists())
    def test_convergence_gate(self):
        with patch('r5_worker.evaluate',side_effect=[{'x':{'unserved_kwh':10}},{'x':{'unserved_kwh':100}}]):
            self.assertFalse(convergence(BASE)['pass_screen'])
    def test_no_regression(self):
        with patch('r5_worker.evaluate',return_value={'x':{'unserved_kwh':20}}):
            self.assertFalse(compare(BASE,{'x':{'unserved_kwh':10}})['nonregression'])
if __name__=='__main__':unittest.main()
