from pathlib import Path
import yaml,json
root=Path('/home/jamie/cwa-weather-proxy/research')
c=yaml.safe_load(Path('/opt/AdGuardHome/AdGuardHome.yaml').read_text())
out={'user_rules':c.get('user_rules',[]),'querylog':c.get('querylog',{}),'querylog_files':[str(p) for p in Path('/opt/AdGuardHome/data').glob('*query*')]}
(root/'adguard-rules-querylog.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
