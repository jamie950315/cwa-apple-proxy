from pathlib import Path
import re
root=Path('/home/jamie/cwa-weather-proxy')
text=(root/'vendor/weatherkit-codec.full.mjs').read_text()
out=[]
for token in ['previousDayComparison(){','EPA_NowCast','categoryIndex(){','primaryPollutant(){','scale:','scale =']:
    indexes=[m.start() for m in re.finditer(re.escape(token),text)]
    out.append('\nTOKEN '+token)
    for index in indexes[-5:]:out.append(text[max(0,index-120):index+650])
(root/'research/aqi-codec-snippets.txt').write_text('\n'.join(out))
