from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def strings(folder):
    return {node.attrib['name']: ''.join(node.itertext()) for node in ET.parse(ROOT / 'hud/res' / folder / 'strings.xml').getroot()}


class LocalizationTests(unittest.TestCase):
    def test_resource_keys_and_format_arguments_match(self):
        english, chinese = strings('values'), strings('values-zh')
        self.assertEqual(english.keys(), chinese.keys())
        pattern = r'%\d+\$[.\d]*[sdf]'
        for key in english:
            self.assertTrue(english[key].strip(), key)
            self.assertTrue(chinese[key].strip(), key)
            self.assertEqual(sorted(re.findall(pattern, english[key])), sorted(re.findall(pattern, chinese[key])), key)
            self.assertIsNone(re.search(r'[\u3400-\u9fff]', english[key]), key)
        self.assertEqual(english['app_name'], 'Playback Info Panel')
        self.assertEqual(chinese['app_name'], '播放信息面板')

    def test_ui_strings_are_resources(self):
        defined = strings('values')
        for source in (ROOT / 'hud/src').rglob('*.java'):
            text = source.read_text()
            self.assertIsNone(re.search(r'[\u3400-\u9fff]', text), str(source))
            for name in re.findall(r'R\.string\.(\w+)', text):
                self.assertIn(name, defined)
        manifest = ET.parse(ROOT / 'hud/AndroidManifest.xml').getroot()
        android = '{http://schemas.android.com/apk/res/android}'
        self.assertEqual(manifest.find('application').attrib[android+'label'], '@string/app_name')

    def test_bilingual_docs_and_release_resources(self):
        from test_release import module
        files = module('release').collect()
        for name in ['README', 'CHANGELOG']:
            self.assertIn(name+'.md', files)
            self.assertIn(name+'.zh-CN.md', files)
        for name in ['privacy', 'architecture', 'validation']:
            self.assertIn('docs/'+name+'.md', files)
            self.assertIn('docs/'+name+'.zh-CN.md', files)
        for folder in ['values', 'values-zh']:
            self.assertIn('hud/res/'+folder+'/strings.xml', files)
        for path in [*ROOT.glob('*.md'), *(ROOT / 'docs').rglob('*.md')]:
            for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' not in link and not link.startswith('#'):
                    self.assertTrue((path.parent / link.split('#')[0]).exists(), f'{path.name}: {link}')
