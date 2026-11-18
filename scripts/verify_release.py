"""Validate source archives without extracting or executing their contents."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from zipfile import ZipFile, BadZipFile


def verify(path):
    path = Path(path)
    expected = path.with_suffix('.zip.sha256').read_text().split()[0]
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError('Archive SHA-256 does not match sidecar')
    with ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) > 1000 or len(names) != len(set(names)) or sum(i.file_size for i in archive.infolist()) > 8*1024*1024:
            raise ValueError('Duplicate entries or archive size bound exceeded')
        roots = {name.split('/')[0] for name in names}
        if len(roots) != 1: raise ValueError('Expected one source root')
        prefix = next(iter(roots)) + '/'
        manifest = json.loads(archive.read(prefix+'SOURCE-MANIFEST.json'))
        if set(names) != {prefix+n for n in manifest} | {prefix+'SOURCE-MANIFEST.json'}:
            raise ValueError('Archive and manifest file lists differ')
        for name, digest in manifest.items():
            relative = PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts or '\\' in name or any(part in {'build','keys','input','diagnostic-logs','.git'} for part in relative.parts):
                raise ValueError('Unsafe source path')
            if name.endswith(('.apk','.p12','.jks','.keystore','.class','.dex','.log','.jsonl','.gz')):
                raise ValueError('Non-source artifact in source archive')
            if hashlib.sha256(archive.read(prefix+name)).hexdigest() != digest:
                raise ValueError('Source hash mismatch: '+name)
        metadata = json.loads(archive.read(prefix+'RELEASE-METADATA.json'))
        if not re.fullmatch(r'\d+\.\d+\.\d+', metadata['version']) or prefix != 'apple-tv-quality-patch-'+metadata['version']+'/':
            raise ValueError('Version/root mismatch')
        return {'version':metadata['version'],'source_commit':metadata['source_commit'],'files':len(manifest)}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('archive');args=parser.parse_args()
    try: print(json.dumps(verify(args.archive),indent=2))
    except (OSError,ValueError,KeyError,IndexError,BadZipFile) as error: parser.exit(1,'Verification failed: '+str(error)+'\n')
