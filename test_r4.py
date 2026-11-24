"""R4 regression tests; run python -m unittest test_r4."""
import json
import unittest
from pathlib import Path
from r4_physics import simulate,commissioning,reliability
from r4_redteam import audit
from r4_optimizer import optimize

class EngineeringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=json.loads(Path("parameter_lock.json").read_text(encoding="utf-8-sig"))
    def test_energy_conservation(self):
        for closed in (False,True):
            r=simulate(self.cfg,aperture_open=not closed)
            self.assertLess(r["relative_balance_error"],1e-9)
    def test_no_energy_no_output(self):
        r=simulate(self.cfg,initial_fraction=0,illumination=0,cycles=1)
        self.assertEqual(r["min_night_kw"],0)
        self.assertEqual(r["mean_night_kw"],0)
    def test_shutter_improves_service(self):
        a=simulate(self.cfg); b=simulate(self.cfg,aperture_open=False)
        self.assertLessEqual(b["unserved_kwh"],a["unserved_kwh"])
    def test_low_efficiency_not_better(self):
        a=simulate(self.cfg,aperture_open=False)
        b=simulate(self.cfg,aperture_open=False,efficiency=.20)
        self.assertGreaterEqual(b["unserved_kwh"],a["unserved_kwh"])
    def test_startup(self):
        self.assertEqual(commissioning(self.cfg)["battery_hours"],10)
        self.assertAlmostEqual(commissioning(self.cfg)["required_battery_kwh"],141.6)
    def test_gate_rejects_unvalidated_design(self):
        self.assertIn("BLOCK",{r["status"] for r in audit(self.cfg)})
    def test_repeatability(self):
        self.assertEqual(reliability(self.cfg,10),reliability(self.cfg,10))
    def test_trade_space(self):
        self.assertEqual(len(optimize(self.cfg)),16)
    def test_timestep_convergence(self):
        a=simulate(self.cfg,dt=900); b=simulate(self.cfg,dt=450)
        self.assertLess(abs(a["unserved_kwh"]-b["unserved_kwh"]),30)
if __name__=="__main__": unittest.main()
