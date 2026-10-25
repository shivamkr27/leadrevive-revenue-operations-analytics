import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from scripts.generate_synthetic_data import AS_OF, generate, write_dataset


class GeneratorTests(unittest.TestCase):
    def test_repeatable_bytes_and_manifest(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            self.assertEqual(write_dataset(a), write_dataset(b))
            self.assertEqual((Path(a)/'leads_SYNTHETIC.csv').read_bytes(),
                             (Path(b)/'leads_SYNTHETIC.csv').read_bytes())

    def test_safe_contacts(self):
        for row in generate():
            self.assertEqual(row['consent_to_email'], 'false')
            self.assertEqual(row['email_verified'], 'false')
            self.assertTrue(row['email'].endswith('.example') or row['email'] == 'invalid-address')
            self.assertTrue(row['phone'].startswith('FICTIONAL-IN-'))

    def test_coverage_and_temporal_consistency(self):
        rows = generate()
        self.assertEqual(len(rows), 800)
        self.assertEqual(len({r['lead_source'] for r in rows}), 5)
        self.assertEqual(len({r['campaign'] for r in rows}), 6)
        self.assertEqual(len({r['owner_id'] for r in rows} - {''}), 4)
        self.assertTrue(any(datetime.fromisoformat(r['created_at']).weekday() >= 5 for r in rows))
        for row in rows:
            created = datetime.fromisoformat(row['created_at'])
            self.assertLessEqual(created, AS_OF)
            if row['last_contacted_at']:
                self.assertLessEqual(created, datetime.fromisoformat(row['last_contacted_at']))
                self.assertLessEqual(datetime.fromisoformat(row['last_contacted_at']), AS_OF)

    def test_expected_edge_cases(self):
        rows = generate()
        counts = {case: sum(r['fixture_case'] == case for r in rows)
                  for case in {r['fixture_case'] for r in rows}}
        self.assertEqual(counts['exact_duplicate'], 7)
        self.assertEqual(counts['conflicting_identity'], 7)
        for case in ['invalid_email', 'missing_company', 'unknown_stage', 'malformed_value']:
            self.assertEqual(counts[case], 8)
        self.assertEqual(rows[100]['lead_id'], rows[0]['lead_id'])
        self.assertEqual(rows[105]['email'], rows[5]['email'])
        self.assertNotEqual(rows[105]['full_name'], rows[5]['full_name'])

    def test_seed_and_count(self):
        self.assertNotEqual(generate(42, 10), generate(43, 10))
        self.assertEqual(len(generate(count=1)), 1)
        with self.assertRaises(ValueError):
            generate(count=0)


if __name__ == '__main__':
    unittest.main()
