import argparse
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile
from atvpatch import __version__, __version_code__
from atvpatch import preflight
from atvpatch.core import validate_video_budget
from atvpatch.patches import ADAPTER

ROOT = Path(__file__).resolve().parents[1]

class PreflightTests(unittest.TestCase):
    def test_missing_environment_is_actionable_and_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = argparse.Namespace(sdk=str(root), build_tools='34.0.0')
            with patch.dict('os.environ', {}, clear=True), patch.object(preflight, 'executable', return_value=None), patch.object(preflight.shutil, 'which', return_value=None):
                result = preflight.doctor(args)
            self.assertFalse(result['ok'])
            self.assertTrue(all(c['remedy'] for c in result['checks'] if not c['ok']))
            self.assertEqual(list(root.iterdir()), [])
            self.assertNotIn(tmp, json.dumps(result))

    def test_unsupported_input_does_not_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); source=root/'original.apk'
            with ZipFile(source, 'w') as archive:
                archive.writestr('assets/app.zip', b'not a bundle')
            before=source.read_bytes()
            result=preflight.inspect_input(argparse.Namespace(input=str(source),sdk=None,build_tools='34.0.0'))
            self.assertFalse(result['ok'])
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(list(root.iterdir()), [source])

    def test_optional_manifest_check_is_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); source=root/'original.apk'; inner=BytesIO()
            with ZipFile(inner,'w') as archive: archive.writestr('synthetic.txt','fixture')
            with ZipFile(source,'w') as archive: archive.writestr('assets/app.zip',inner.getvalue())
            with patch.dict('os.environ',{},clear=True), patch.object(preflight,'patch_assets',return_value={}):
                result=preflight.inspect_input(argparse.Namespace(input=str(source),sdk=None,build_tools='34.0.0'))
            self.assertTrue(result['ok'])
            self.assertFalse(result['manifest_verified'])
            self.assertIn('Manifest not checked', ' '.join(result['messages']))

    def test_profiles_and_version_contract(self):
        self.assertEqual(ADAPTER['version_code'], '143100')
        for name, budget in [('platform',0),('sony-x75j',128)]:
            data=json.loads((ROOT/'atvpatch/profiles'/f'{name}.json').read_text())
            self.assertEqual(validate_video_budget(data['video_buffer_mib']),budget)
        self.assertEqual(__version__, '0.2.0')
        self.assertEqual(__version_code__, 200)
        for invalid in (True, False, '128', 15, 257):
            with self.assertRaises(ValueError): validate_video_budget(invalid)
