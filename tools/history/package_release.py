from pathlib import Path
import hashlib,json,re,zipfile,importlib.metadata,subprocess,time
ROOT=Path('/home/jamie/cwa-weather-proxy')
(ROOT/'dist').mkdir(exist_ok=True)
(ROOT/'.env.example').write_text('CWA_API_KEY=\n')
(ROOT/'requirements.lock').write_text('\n'.join(sorted(f'{d.metadata["Name"]}=={d.version}' for d in importlib.metadata.distributions()))+'\n')
(ROOT/'systemd').mkdir(exist_ok=True)
for unit in ['api','codec','proxy','forward','sni','routing']:
 name='cwa-weather-'+unit+'.service'
 (ROOT/'systemd'/name).write_text((Path('/etc/systemd/system')/name).read_text())
files=['README.md','package.json','.env.example','requirements.lock','mapper.mjs','codec_server.mjs','addon.py','api.py','cwa_model.py','cwa_client.py','cwa_snapshot.py','cwa_regions.json','town_index.json','sni_router.py','network_rules.py','bridgectl.py','dashboard.html','config/apple-prefixes.json','vendor/weatherkit-codec.full.mjs','vendor/LICENSE-WeatherKit','vendor/NOTICE','research/actual-brief.json','research/apple-1789067343103901835.bin','research/verify_release.py','research/verify_native.mjs','research/bootstrap_probe.py']
files += [str(p.relative_to(ROOT)) for p in (ROOT/'tests').glob('*') if p.is_file()]
files += [str(p.relative_to(ROOT)) for p in (ROOT/'systemd').glob('*.service')]
files += [str(p.relative_to(ROOT)) for p in (ROOT/'reports').rglob('*') if p.is_file()]
for name in ['release-verification.json','town-matrix-v2.json']:
 p=ROOT/'research'/name
 if p.exists():files.append(str(p.relative_to(ROOT)))
pattern=re.compile(rb'CWA-[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
manifest={}
for name in sorted(set(files)):
 p=ROOT/name;data=p.read_bytes()
 if pattern.search(data) or b'BEGIN PRIVATE KEY' in data or b'BEGIN RSA PRIVATE KEY' in data:
  raise RuntimeError('Sensitive content detected in '+name)
 manifest[name]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
(ROOT/'dist/manifest.json').write_text(json.dumps({'version':'0.2.0','createdAt':int(time.time()),'files':manifest},ensure_ascii=False,indent=2))
archive=ROOT/'dist/cwa-weather-bridge-source.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for name in sorted(manifest):z.write(ROOT/name,'cwa-weather-bridge/'+name)
 z.write(ROOT/'dist/manifest.json','cwa-weather-bridge/MANIFEST.json')
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert all('/certs/' not in n and not n.endswith('/.env') and '/backups/' not in n for n in z.namelist())
print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'fileCount':len(manifest),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'secretScan':'passed'},indent=2))
