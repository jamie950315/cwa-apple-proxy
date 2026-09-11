from pathlib import Path
import json
R=Path('/home/jamie/cwa-weather-proxy');out={}
for name in ['臺北','臺南','桃園']:
    d=json.loads((R/'research'/('live031-'+name+'.json')).read_text())
    out[name]={'aqi':d.get('airQuality'),'nwp':None,'astronomyDays':len(d.get('astronomy',{}).get('days',[]))}
    n=d.get('nwp')
    if n:out[name]['nwp']={'initialTime':n['initialTime'],'pressurePoints':len(n['points']),'rainIntervals':len(n['rainIntervals']),'firstRain':n['rainIntervals'][:1],'lastRain':n['rainIntervals'][-1:],'grid':n.get('grid')}
(R/'reports/new-source-summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
