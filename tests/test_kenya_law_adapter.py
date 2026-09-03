from pathlib import Path
import sys, unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from world_signals.adapters import AdapterError, parse_kenya_budget_policy_rule

class KenyaLawAdapterTests(unittest.TestCase):
    def test_extracts_section_25_deadline(self):
        html='''<html><body><h1>Public Finance Management Act</h1><h3>25. National Treasury to prepare annual Budget Policy Statement</h3><p>(2) The National Treasury shall submit the Budget Policy Statement approved in terms of subsection (1) to Parliament, by the 15th February in each year.</p></body></html>'''
        rule=parse_kenya_budget_policy_rule(html)
        self.assertEqual(rule.section,"25(2)")
        self.assertEqual((rule.deadline_month,rule.deadline_day),(2,15))
        self.assertEqual(len(rule.rule_sha256),64)

    def test_unrelated_amendment_does_not_change_semantic_rule_hash(self):
        base='''<html><body><h1>Public Finance Management Act</h1><p>Other provision A.</p><p>The National Treasury shall submit the Budget Policy Statement approved in terms of subsection (1) to Parliament, by the 15th February in each year.</p></body></html>'''
        changed='''<html><body><h1>Public Finance Management Act</h1><p>Other provision A was amended substantially.</p><p>The National Treasury shall submit the Budget Policy Statement approved in terms of subsection (1) to Parliament, by the 15th February in each year.</p></body></html>'''
        self.assertEqual(parse_kenya_budget_policy_rule(base).rule_sha256,parse_kenya_budget_policy_rule(changed).rule_sha256)

    def test_missing_rule_is_quarantined(self):
        html='<html><body><h1>Public Finance Management Act</h1><p>No budget deadline here.</p></body></html>'
        with self.assertRaises(AdapterError):
            parse_kenya_budget_policy_rule(html)

if __name__=="__main__": unittest.main()
