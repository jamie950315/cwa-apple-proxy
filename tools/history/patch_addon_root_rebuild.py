from pathlib import Path
p=Path('/home/jamie/cwa-weather-proxy/addon.py');s=p.read_text()
s=s.replace("if len(body)!=len(original):raise ValueError('Codec changed buffer length')\n            report=mapped['report']","report=mapped['report']\n            if len(body)!=len(original) and not report.get('rebuiltRoots'):raise ValueError('Codec changed buffer length without verified root rebuild')\n            if not 12<=len(body)<=4_000_000:raise ValueError('Codec output size invalid')")
p.write_text(s)
