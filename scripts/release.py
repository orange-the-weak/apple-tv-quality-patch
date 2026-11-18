"""Build an allowlisted source-only archive, without Git or network operations."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import argparse
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from atvpatch import __version__, RELEASE_DATE
ROOT_FILES = ['README.md', 'README.zh-CN.md', 'LICENSE', 'NOTICE', 'CHANGELOG.md', 'CHANGELOG.zh-CN.md', '.gitignore', 'pyproject.toml', 'CONTRIBUTING.md', 'CONTRIBUTING.zh-CN.md', 'SECURITY.md', 'SECURITY.zh-CN.md', 'CODE_OF_CONDUCT.md']
PATTERNS = ['atvpatch/**/*.py', 'atvpatch/adapters/*.json', 'atvpatch/profiles/*.json', 'atvpatch/payloads/*.js', 'hud/src/**/*.java', 'hud/res/**/*.xml', 'hud/AndroidManifest.xml', 'scripts/*.py', 'scripts/*.sh', 'tests/*.py', 'tests/*.java', 'tests/*.js', 'docs/**/*.md', 'docs/assets/*.svg', '.github/**/*.yml', '.github/*.md']


def collect(root=ROOT):
    paths = {root / name for name in ROOT_FILES}
    for pattern in PATTERNS:
        paths.update(root.glob(pattern))
    files = {}
    for path in sorted(paths):
        if not path.is_file() or path.is_symlink() or root.resolve() not in path.resolve().parents:
            raise ValueError('Invalid source path: ' + path.name)
        data = path.read_bytes()
        if len(data) > 100000:
            raise ValueError('Unexpected large source file: ' + path.name)
        text = data.decode('utf-8')
        if re.search(r'/Users/[A-Za-z0-9_.-]+|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}|^-----BEGIN .*PRIVATE KEY-----', text, re.M):
            raise ValueError('Personal data or private key marker in: ' + path.name)
        for match in re.finditer(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text):
            if match.group() != '127.0.0.1':
                raise ValueError('Device IP in source: ' + path.name)
        files[path.relative_to(root).as_posix()] = data
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-tag", action="store_true", help="Require a clean checkout of the exact version tag")
    args = parser.parse_args()
    def git(*command):
        result = subprocess.run(["git", *command], cwd=ROOT, text=True, capture_output=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else None
    commit = git("rev-parse", "HEAD")
    if args.require_tag:
        if git("describe", "--tags", "--exact-match", "HEAD") != "v"+__version__ or git("status", "--porcelain") != "":
            parser.error("Release requires a clean checkout of tag v"+__version__)
    files = collect()
    files["RELEASE-METADATA.json"] = (json.dumps({"version":__version__,"source_commit":commit,"status":"public-preview","vendor_assets_included":False},indent=2)+"\n").encode()
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    files['SOURCE-MANIFEST.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    out = ROOT / 'dist'
    out.mkdir(exist_ok=True)
    target = out / ('apple-tv-quality-patch-'+__version__+'-source.zip')
    temporary = target.with_suffix('.zip.partial')
    try:
        with ZipFile(temporary, 'w', compression=ZIP_DEFLATED) as archive:
            for name, data in sorted(files.items()):
                info = ZipInfo('apple-tv-quality-patch-'+__version__+'/' + name, date_time=RELEASE_DATE)
                info.compress_type = ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    target.with_suffix('.zip.sha256').write_text(digest + '  ' + target.name + '\n')
    print('Source-only archive:', target)
    print('SHA256:', digest)


if __name__ == '__main__':
    main()
