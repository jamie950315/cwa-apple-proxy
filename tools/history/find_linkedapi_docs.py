import httpx,ssl,re,pathlib,html
ctx=ssl.create_default_context();ctx.verify_flags &= ~getattr(ssl,'VERIFY_X509_STRICT',0)
with httpx.Client(verify=ctx,timeout=20,trust_env=False) as c:
 for url in ['https://opendata.cwa.gov.tw/devManual/insrtuction','https://opendata.cwa.gov.tw/devManual/datalist']:
  t=c.get(url).text
  pathlib.Path('/home/jamie/cwa-weather-proxy/research/'+url.rsplit('/',1)[-1]+'.html').write_text(t)
  print('\n',url)
  for m in re.finditer(r'href=["\']([^"\']+)["\']',t,re.I):
   h=html.unescape(m.group(1))
   if any(x in h.lower() for x in ['graphql','linked','api']):print(h)
  for line in t.splitlines():
   if any(x in line.lower() for x in ['graphql','linkedapi','l-003','l-007']):print(re.sub('<[^>]+>',' ',line)[:1200])
