from io import BytesIO
from zipfile import ZipFile
import unittest
from unittest.mock import patch
from atvpatch.patches import PatchError, patch_assets
from atvpatch.build import rewrite

class PatchTests(unittest.TestCase):
    def test_unsupported_input_fails_closed(self):
        out = BytesIO()
        with ZipFile(out, 'w') as z:
            z.writestr('app-worker.chunk.js', 'unrecognized version')
            z.writestr('hls-adopted.chunk.js', 'unrecognized version')
        with ZipFile(BytesIO(out.getvalue())) as z:
            with self.assertRaisesRegex(PatchError, 'Unsupported|Missing'):
                patch_assets(z)

    def test_video_budget_rejects_invalid_values_before_reading_assets(self):
        for value in [-1, 1, 257, 128.5, '128']:
            with self.subTest(value=value), self.assertRaisesRegex(PatchError, 'video_buffer_mib'):
                patch_assets(None, video_buffer_mib=value)

    def test_rewrite_preserves_binary_and_removes_old_signature(self):
        out = BytesIO()
        with ZipFile(out, 'w') as z:
            for name, data in {'classes.dex': b'\x00dex', 'lib/a.so': b'\xffnative', 'META-INF/CERT.RSA': b'old', 'META-INF/MANIFEST.MF': b'old', 'asset.js': b'old'}.items():
                z.writestr(name, data)
        with ZipFile(BytesIO(rewrite(out.getvalue(), {'asset.js': b'new'}))) as z:
            self.assertEqual(z.read('classes.dex'), b'\x00dex')
            self.assertEqual(z.read('lib/a.so'), b'\xffnative')
            self.assertEqual(z.read('asset.js'), b'new')
            self.assertNotIn('META-INF/CERT.RSA', z.namelist())
            self.assertNotIn('META-INF/MANIFEST.MF', z.namelist())

    def test_source_up_event_is_not_consumed(self):
        from pathlib import Path
        s = (Path(__file__).resolve().parents[1] / 'hud/src/local/tv/playbackpanel/PanelService.java').read_text()
        callback = s.split('protected boolean onKeyEvent', 1)[1].split('private void toggle()', 1)[0]
        self.assertIn('return false;', callback)
        self.assertIn('HudKeyPolicy.isInfoKey', callback)
        self.assertTrue(callback.strip().endswith('}'))

if __name__ == '__main__':
    unittest.main()
