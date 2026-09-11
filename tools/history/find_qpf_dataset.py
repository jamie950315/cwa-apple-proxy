import httpx,ssl,re,urllib.parse,pathlib
ctx=ssl.create_default_context();ctx.verify_flags &= ~getattr(ssl,'VERIFY_X509_STRICT',0)
out=[]
with httpx.Client(verify=ctx,timeout=20,trust_env=False) as c:
 for q in ['定量降水格點預報資料','約每2.5公里','未來6小時']:
  u='https://opendata.cwa.gov.tw/dataset/forecast?searchValue='+urllib.parse.quote(q)
  r=c.get(u);out.append(f'URL {r.url} {r.status_code} {len(r.text)}')
  out.extend(sorted(set(re.findall(r'[A-Z]-[A-Z]\d{4}-\d{3}',r.text))))
  for m in re.finditer('定量降水格點',r.text):out.append(re.sub(r'<[^>]*>',' ',r.text[max(0,m.start()-1000):m.start()+2500])[:3500])
pathlib.Path('/home/jamie/cwa-weather-proxy/research/qpf-dataset-discovery.txt').write_text('\n'.join(out))
print('\n'.join(out))
