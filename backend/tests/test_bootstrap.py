"""A new-clone bootstrap must never mutate an existing installation."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.bootstrap_demo import main


class BootstrapTests(unittest.TestCase):
    def test_populated_database_skips_seed_and_migrations(self):
        with tempfile.TemporaryDirectory() as temp:
            database=Path(temp)/'existing.sqlite'
            with sqlite3.connect(database) as conn:
                conn.execute('CREATE TABLE leads (lead_id TEXT PRIMARY KEY, note TEXT)')
                conn.execute("INSERT INTO leads VALUES ('preserved', 'existing audit context')")
            conn.close()
            before=database.read_bytes()
            with patch.dict(os.environ,{'DATABASE_URL':'sqlite:///'+database.as_posix()}),patch('scripts.seed_db.main') as seed,patch('alembic.command.upgrade') as upgrade:
                main();seed.assert_not_called();upgrade.assert_not_called()
            self.assertEqual(before,database.read_bytes())

    def test_missing_database_url_refuses_implicit_bootstrap(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(RuntimeError,'Explicit DATABASE_URL'):main()
