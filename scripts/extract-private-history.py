#!/usr/bin/env python3
"""Extract local handoff evidence safely without executing historical scripts."""
import argparse,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('archive',choices=['history','native-evidence'])
a=p.parse_args();archive=ROOT/'.private'/(a.archive+'.tar.gz');dest=ROOT/'.private/extracted'/a.archive
if not archive.is_file():raise SystemExit('Private archive is available only in the original Mac working tree.')
if dest.exists():raise SystemExit('Destination already exists; inspect it before repeating extraction.')
dest.mkdir(parents=True,mode=0o700)
with tarfile.open(archive,'r:gz') as tar:
    for member in tar.getmembers():
        path=Path(member.name)
        if path.is_absolute() or '..' in path.parts or not member.isfile():raise SystemExit('Unsafe archive member')
    tar.extractall(dest,filter='data')
print(dest)
