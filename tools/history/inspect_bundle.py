from pathlib import Path
p=Path('/home/jamie/cwa-weather-proxy')
s=(p/'research/response.bundle.js').read_text()
with (p/'research/bundle-snippets.txt').open('w') as f:
 for token in ['name:"WeatherKit2"','Nt=new','const Nt','application/vnd.apple.flatbuffer','getRootAsWeather','class y','class S']:
  start=0
  for _ in range(3):
   i=s.find(token,start)
   if i<0:break
   print('\nTOKEN',token,'AT',i,'\n',s[max(0,i-250):i+1400],file=f);start=i+len(token)
