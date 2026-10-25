import hashlib
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from scripts.prepare_powerbi import prepare,ROOT


class PowerBIPortabilityTests(unittest.TestCase):
    def test_relocated_folder_preserves_visuals_and_verifies_all_inputs(self):
        original=ROOT/'analytics/powerbi/phase5'
        before={p.relative_to(original).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in original.rglob('*') if p.is_file()}
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'folder with spaces'/'portable'
            exports=Path(temp)/'relocated clone'/'exports'
            from backend.app.artifacts import current_dir
            generation=current_dir()
            shutil.copytree(generation,exports/'generations'/generation.name)
            shutil.copy2(ROOT/'analytics/exports/current.json',exports/'current.json')
            proof=prepare(target,exports=exports)
            self.assertEqual(len(proof['inputs']),6)
            model=json.loads((target/'LeadRevive.SemanticModel/model.bim').read_text())
            paths=[]
            for table in model['model']['tables']:
                for partition in table.get('partitions',[]):
                    paths.extend(re.findall(r'File\.Contents\("([^"]+)"\)','\n'.join(partition['source'].get('expression',[]))))
            self.assertEqual(len(paths),6)
            self.assertTrue(all(Path(p).is_file() for p in paths))
            self.assertTrue(all(Path(p).is_relative_to(exports) for p in paths))
            for name,digest in before.items():
                self.assertEqual(hashlib.sha256((original/name).read_bytes()).hexdigest(),digest)
                if name!='LeadRevive.SemanticModel/model.bim' and '.pbi/' not in name:
                    self.assertEqual(hashlib.sha256((target/name).read_bytes()).hexdigest(),digest)
            self.assertNotEqual(proof['original_model_sha256'],proof['derived_model_sha256'])
            with self.assertRaisesRegex(ValueError,'already exists'):prepare(target)

    def test_missing_generation_creates_no_output(self):
        with tempfile.TemporaryDirectory() as temp:
            target=Path(temp)/'unused'
            with self.assertRaises(ValueError):prepare(target,generation='0'*32)
            self.assertFalse(target.exists())

    def test_output_inside_originals_is_refused(self):
        with self.assertRaisesRegex(ValueError,'outside preserved'):
            prepare(ROOT/'analytics/powerbi/phase5/never-create-portable')
