#!/usr/bin/env python3
"""Offline repository integrity and credential checks; --staged reads actual Git index bytes."""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
CREDENTIAL=re.compile(rb'CWA-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
PRIVATE=re.compile(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----[\r\n]')
FORBIDDEN={'.private','certs','backups','data','logs','.venv','node_modules','__pycache__'}
SENSITIVE={'clients.json','config/managed-dns-rules.json','config/split-route-state.json'}
REQUIRED=['AGENTS.md','README.md','versions.json','mapper.mjs','addon.py','api.py','cwa_client.py','cwa_snapshot.py','model_worker.py','network_rules.py','split_routes.py','bridgectl.py','flatbuffer_expand.mjs','sni_router.py','codec_server.mjs','weather_math.mjs','cwa_regions.json','town_index.json','requirements.production-linux.lock','requirements.development.lock','vendor/weatherkit-codec.full.mjs','vendor/LICENSE-WeatherKit','vendor/NOTICE','docs/STATUS.md','docs/ARCHITECTURE.md','docs/OPERATIONS.md','docs/NETWORKING.md','docs/DATA_SOURCES.md','docs/KNOWN_ISSUES.md','docs/DEVELOPMENT.md','docs/VALIDATION.md','docs/DECISIONS.md','docs/SECURITY.md','docs/PROVENANCE.md','docs/CHANGELOG.md','infra/snapshots/tailscale-serve.json']
def git(args):
    return subprocess.check_output(['git','-C',str(ROOT),*args],stderr=subprocess.DEVNULL)
def work_files():
    # Prune ignored directories before reading any private bytes.
    import os
    for base,dirs,names in os.walk(ROOT):
        dirs[:]=[d for d in dirs if d not in FORBIDDEN|{'.git','.pytest_cache'}]
        for name in names:
            p=Path(base)/name;rel=p.relative_to(ROOT).as_posix()
            if p.is_symlink() or rel in SENSITIVE:continue
            if name.startswith('.env') and name!='.env.example':continue
            yield rel,p.read_bytes()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--staged',action='store_true');a=p.parse_args()
    errors=[];warnings=[];count=0
    if a.staged:
        names=[x.decode() for x in git(['ls-files','--cached','-z']).split(b'\0') if x]
        files=((name,git(['show',':'+name])) for name in names)
    else:files=work_files()
    for name,blob in files:
        count+=1;path=Path(name)
        if any(x in FORBIDDEN for x in path.parts) or name in SENSITIVE or (path.name.startswith('.env') and path.name!='.env.example'):
            errors.append('Forbidden staged path: '+name)
        if CREDENTIAL.search(blob) or PRIVATE.search(blob):errors.append('Credential material: '+name)
    for name in REQUIRED:
        if not (ROOT/name).is_file():errors.append('Missing required file: '+name)
    for path in ROOT.glob('*.py'):
        try:compile(path.read_text(),str(path),'exec')
        except SyntaxError as e:errors.append('Python syntax: '+path.name+': '+str(e))
    info=json.loads((ROOT/'research/actual-brief.json').read_text())
    fixture=ROOT/'research'/('apple-'+str(info['source']['id'])+'.bin')
    if not fixture.is_file() or fixture.stat().st_size<12:errors.append('Missing native fixture')
    links=0
    for path in [ROOT/'README.md',ROOT/'AGENTS.md',*(ROOT/'docs').glob('*.md')]:
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)',path.read_text()):
            if '://' in target or target.startswith('#'):continue
            target=target.split('#',1)[0];links+=1
            if target and not (path.parent/target).exists():errors.append('Broken link: '+path.name+': '+target)
    manifest=json.loads((ROOT/'docs/evidence/production-source-manifest.json').read_text());verified=0
    intentional={'README.md','package.json','.env.example'}
    for row in manifest['files']:
        if row['repo'] in intentional:continue
        dest=ROOT/row['repo']
        if not dest.is_file():errors.append('Missing copied source: '+row['repo']);continue
        if hashlib.sha256(dest.read_bytes()).hexdigest()!=row['sha256Copied']:
            warnings.append('Source changed since initial production snapshot: '+row['repo'])
        else:verified+=1
    result={'status':'passed' if not errors else 'failed','scannedFiles':count,'productionFilesMatchingSnapshot':verified,'documentationLinksChecked':links,'errors':errors,'warnings':warnings}
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
