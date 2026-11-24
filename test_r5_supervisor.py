import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import r5_supervisor as supervisor
from r5_supervisor import BASE, screen, improves, choose, scenarios


def fake(timeline, **kwargs):
    shortage=0 if kwargs['mass']>=250000 else 100
    return dict(minimum_bus_kw=10.5 if not shortage else 0,unserved_kwh=shortage,relative_energy_residual=0)

class SupervisorTests(unittest.TestCase):
    def test_relative_faults(self):
        self.assertEqual(scenarios(BASE|{'collector':200})['optical'][1]['collector'],160)
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):
            screen(BASE,lambda *a,**k:dict(minimum_bus_kw=float('nan'),unserved_kwh=0,relative_energy_residual=0))
    def test_energy_error_rejected(self):
        with self.assertRaises(ValueError):
            screen(BASE,lambda *a,**k:dict(minimum_bus_kw=10.5,unserved_kwh=0,relative_energy_residual=.01))
    def test_no_regression(self):
        b=screen(BASE,fake); c=screen(BASE|{'mass':250000},fake)
        self.assertTrue(improves(c,b)); self.assertFalse(improves(b,c)); self.assertFalse(improves(b,b))
    def test_candidate_and_holdout(self):
        r=choose(fake);self.assertEqual(len(r['candidates']),12);self.assertEqual(r['selected']['design']['mass'],250000);self.assertTrue(r['screen_pass'])
    def test_no_candidate(self):
        r=choose(lambda *a,**k:fake([],mass=125000));self.assertIsNone(r['selected']);self.assertFalse(r['screen_pass'])
    def test_holdout_blocks(self):
        def solver(timeline,**k):
            return fake(timeline,**(k|{'mass':125000})) if timeline[0]==0 else fake(timeline,**k)
        self.assertFalse(choose(solver)['screen_pass'])

    def test_stop_on_unexpected_exit(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(supervisor,'ROOT',Path(tmp)), patch.object(supervisor,'run_job',return_value={'exit':1,'stdout':'','stderr':'crash'}) as job, patch.object(supervisor,'choose') as search:
            self.assertEqual(supervisor.main(),1);self.assertEqual(job.call_count,1);search.assert_not_called()
            self.assertEqual(json.loads((Path(tmp)/'r5_supervisor_report.json').read_text())['status'],'STOPPED_ERROR')
    def test_review_stops_even_when_screen_passes(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(supervisor,'ROOT',Path(tmp)), patch.object(supervisor,'run_job',return_value={'exit':0,'stdout':'','stderr':''}), patch.object(supervisor,'choose',return_value={'screen_pass':True}):
            root=Path(tmp)
            for name in ('r4_mission.py','r5_supervisor.py','r5_reliability.py'): (root/name).write_text('test')
            (root/'r5_requirements.json').write_text(json.dumps([{'id':'test','status':'OPEN'}]))
            self.assertEqual(supervisor.main(),2)
            r=json.loads((root/'r5_supervisor_report.json').read_text());self.assertEqual(r['status'],'STOPPED_REVIEW_REQUIRED');self.assertEqual(r['open_requirements'],['test'])

if __name__=='__main__': unittest.main()
