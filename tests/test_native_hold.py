"""Optional integration test using user-supplied vendor assets; never stores them in source."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from io import BytesIO
from zipfile import ZipFile
from atvpatch.patches import patch_assets


def methods(source, name):
    marker = name + '(e,t){'
    result = []
    start = 0
    while True:
        found = source.find(marker, start)
        if found < 0:
            return result
        body = found + len(marker) - 1
        depth, quote, escaped = 0, None, False
        for i in range(body, len(source)):
            char = source[i]
            if quote:
                if escaped: escaped = False
                elif char == '\\': escaped = True
                elif char == quote: quote = None
            elif char in ('"', "'", '`'): quote = char
            elif char == '{': depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    result.append('function(e,t)' + source[body:i+1])
                    start = i+1
                    break
        else:
            raise ValueError('Unclosed native method')


class NativeHoldTests(unittest.TestCase):
    @unittest.skipUnless(os.environ.get('ATV_TEST_APK'), 'ATV_TEST_APK not supplied; no vendor fixtures distributed')
    def test_reader_mode_short_and_long_paths(self):
        with ZipFile(os.environ['ATV_TEST_APK']) as apk, ZipFile(BytesIO(apk.read('assets/app.zip'))) as assets:
            patched = patch_assets(assets, video_buffer_mib=128)
            source = patched['PlayerPage.js'].decode()
            hls = patched['hls-adopted.chunk.js'].decode()
        import re
        water = re.search(r'function Gg\(e,t,i,r\)\{[^{}]+\}', hls)
        self.assertIsNotNone(water)
        code = 'const assert=require("node:assert/strict");const water=('+water.group()+');'
        code += 'assert.equal(water(6,54,12,{paused:true,stopStreaming:false}),54);'
        code += 'assert.equal(water(6,54,12,{paused:false,stopStreaming:false}),54);'
        code += 'assert.equal(water(6,54,12,{paused:true,stopStreaming:true}),12);'
        subprocess.run(['node','-e',code],check=True,capture_output=True,text=True,timeout=5)
        worker = patched['app-worker.chunk.js'].decode()
        expression = re.search(r'this.maxBufferSize=\(r.type===\"video\"\?Math.max\(this.maxBufferSize,134217728\):this.maxBufferSize\)', worker)
        self.assertIsNotNone(expression)
        code = 'const assert=require("node:assert/strict");function alloc(r){'+expression.group()+';return this.maxBufferSize;}'
        code += 'assert.equal(alloc.call({maxBufferSize:83886080},{type:"video"}),134217728);'
        code += 'assert.equal(alloc.call({maxBufferSize:5242880},{type:"audio"}),5242880);'
        code += 'assert.equal(alloc.call({maxBufferSize:268435456},{type:"video"}),268435456);'
        subprocess.run(['node','-e',code],check=True,capture_output=True,text=True,timeout=5)
        native = methods(source, 'keyHandlingSeekOrTrickplay')
        self.assertEqual(len(native), 2)
        with tempfile.TemporaryDirectory() as folder:
            fixture = Path(folder) / 'native-methods.json'
            fixture.write_text(json.dumps(native))
            script = Path(__file__).with_name('native-hold.test.js')
            subprocess.run(['node', str(script), str(fixture)], check=True, capture_output=True, text=True, timeout=10)
