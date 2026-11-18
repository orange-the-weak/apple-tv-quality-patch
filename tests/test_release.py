import importlib.util
from pathlib import Path
import tempfile
import time
import unittest
import os

ROOT = Path(__file__).resolve().parents[1]

def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

class ReleaseTests(unittest.TestCase):
    def test_archive_allowlist_omits_artifacts_and_keys(self):
        release = module('release')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in release.ROOT_FILES:
                (root / name).write_text('public source')
            (root / 'build').mkdir(); (root / 'keys').mkdir()
            (root / 'build/vendor.apk').write_bytes(b'private APK')
            (root / 'keys/local.p12').write_bytes(b'private key')
            files = release.collect(root)
            self.assertEqual(set(files), set(release.ROOT_FILES))
            (root / 'README.md').write_text('/Users/' + 'private-user/path')
            with self.assertRaises(ValueError):
                release.collect(root)

    def test_export_retention_is_bounded_and_scoped(self):
        device = module('device')
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp); now = time.time()
            for i in range(10):
                path = folder / f'playback-{i}.jsonl.gz'
                with path.open('wb') as out:
                    out.truncate(9 * 1024 * 1024)
                os.utime(path, (now-i, now-i))
            old = folder / 'playback-old.jsonl.gz'; old.write_bytes(b'old')
            os.utime(old, (now-8*86400, now-8*86400))
            unrelated = folder / 'keep.txt'; unrelated.write_text('keep')
            device.retain(folder, now)
            files = list(folder.glob('playback-*.jsonl.gz'))
            self.assertLessEqual(sum(p.stat().st_size for p in files), 64*1024*1024)
            self.assertEqual(len(files), 7)
            self.assertFalse(old.exists())
            self.assertEqual(unrelated.read_text(), 'keep')
            device.retain(folder, now)
            self.assertEqual(len(list(folder.glob('playback-*.jsonl.gz'))), 7)


    def test_export_recovers_zero_filled_and_partial_lines(self):
        device = module('device')
        valid = '{"type":"sample","data":{"bitrate":25000000}}'
        text = "BEGIN_PLAYBACK_JSONL\n" + "\x00"*30 + valid + "\n" + '{"type":' + "\nEND_PLAYBACK_JSONL\n"
        rows, skipped = device.parse_diagnostic_dump(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['data']['bitrate'], 25000000)
        self.assertEqual(skipped, 1)


    def test_archive_verifier_rejects_tampering(self):
        import hashlib
        import json
        from zipfile import ZipFile
        verify = module('verify_release').verify
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.zip'; prefix='apple-tv-quality-patch-0.2.0/'
            metadata=json.dumps({'version':'0.2.0','source_commit':None}).encode()
            files={'RELEASE-METADATA.json':metadata,'README.md':b'original'}
            manifest={name:hashlib.sha256(data).hexdigest() for name,data in files.items()}
            def write(tamper=False):
                with ZipFile(path,'w') as archive:
                    for name,data in files.items(): archive.writestr(prefix+name,b'changed' if tamper and name=='README.md' else data)
                    archive.writestr(prefix+'SOURCE-MANIFEST.json',json.dumps(manifest))
                path.with_suffix('.zip.sha256').write_text(hashlib.sha256(path.read_bytes()).hexdigest()+'  source.zip\n')
            write(); self.assertEqual(verify(path)['version'],'0.2.0')
            write(True)
            with self.assertRaisesRegex(ValueError,'Source hash mismatch'): verify(path)
            write(); path.write_bytes(path.read_bytes()+b'tampered')
            with self.assertRaisesRegex(ValueError,'Archive SHA-256'): verify(path)
