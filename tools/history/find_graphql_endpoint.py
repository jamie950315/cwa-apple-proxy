import httpx,ssl,re,pathlib
ctx=ssl.create_default_context();ctx.verify_flags &= ~getattr(ssl,'VERIFY_X509_STRICT',0)
urls=['https://opendata.cwa.gov.tw/devManual/datalist','https://opendata.cwa.gov.tw/devManual/insrtuction','https://opendata.cwa.gov.tw/linkedapi']
out=[]
with httpx.Client(verify=ctx,timeout=20,follow_redirects=True,trust_env=False) as c:
 for u in urls:
  try:
   r=c.get(u);out.append(f'URL {u} {r.status_code} {r.url}')
   for s in re.findall(r'<script[^>]+src=["\']([^"\']+)',r.text,re.I):out.append('SCRIPT '+s)
   for pattern in ['graphql','linkedapi','/api/']:
    for m in re.finditer(pattern,r.text,re.I):out.append('SNIP '+re.sub(r'\s+',' ',r.text[max(0,m.start()-250):m.start()+500]))
  except Exception as e:out.append(type(e).__name__+':'+str(e))
pathlib.Path('/home/jamie/cwa-weather-proxy/research/graphql-discovery.txt').write_text('\n'.join(out))
print('\n'.join(out)[:20000])
