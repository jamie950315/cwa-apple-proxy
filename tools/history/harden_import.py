from pathlib import Path
root=Path('/home/jamie/cwa-weather-proxy')
p=root/'addon.py';s=p.read_text().replace('maxBytes=5000000,backupCount=2)','maxBytes=5000000,backupCount=2,delay=True)');p.write_text(s)
p=root/'research/finalize_runtime.py';s=p.read_text().replace("[str(ROOT/'.venv/bin/python'),'-m','pytest','-q']","['sudo','-u','jamie',str(ROOT/'.venv/bin/python'),'-m','pytest','-q']");p.write_text(s)
p=root/'research/deploy_v2.py';s=p.read_text().replace("run([str(ROOT/'.venv/bin/python'),'-m','pytest','-q'])","run(['sudo','-u','jamie',str(ROOT/'.venv/bin/python'),'-m','pytest','-q'])");p.write_text(s)
print('Log file opened lazily; tests run as daemon owner')
