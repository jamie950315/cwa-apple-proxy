import httpx,ssl,re
ctx=ssl.create_default_context();ctx.verify_flags &= ~getattr(ssl,'VERIFY_X509_STRICT',0)
with httpx.Client(verify=ctx,timeout=20,trust_env=False) as c:
 t=c.get('https://opendata.cwa.gov.tw/dist/opendata-swagger.html').text
 for pat in ['url:', 'swagger', '.json']:
  print('\nPAT',pat)
  for line in t.splitlines():
   if pat.lower() in line.lower(): print(line[:1200])
