from pathlib import Path
R=Path('/home/jamie/cwa-weather-proxy');p=R/'addon.py';s=p.read_text().replace("VERSION='0.3.0'","VERSION='0.3.1'")
s=s.replace("original=flow.response.content;headers=", "original=flow.response.content;original_raw=flow.response.raw_content;headers=")
s=s.replace("flow.response.content=original;flow.response.headers=headers", "flow.response.raw_content=original_raw;flow.response.headers=headers")
s=s.replace("            report=mapped['report']", "            if time.monotonic()-started>DEADLINE:raise TimeoutError('translation deadline')\n            report=mapped['report']")
s=s.replace("if not report['modifiedFields']:self.stats", "if not report['modifiedFields'] and not report.get('rebuiltRoots'):self.stats")
s=s.replace("        except Exception:self.stats['notificationErrors']+=1", """        except Exception:
            self.stats['notificationErrors']+=1
        else:
            try:
                payload={'time':int(time.time()),'mode':MODE,'topic':'cwa-apple-proxy','http':r.status_code,'receiptId':r.json().get('id'),'reason':reason,'elapsedMs':event.get('elapsedMs')}
                temp=ROOT/'data'/('notification-'+uuid.uuid4().hex+'.tmp');temp.write_text(json.dumps(payload));temp.replace(ROOT/'data/notification-last.json')
            except (OSError,ValueError):pass""")
p.write_text(s)
p=R/'api.py';s=p.read_text();s=s.replace("result['clients']=read_json", "result['notification']=read_json(ROOT/'data/notification-last.json',{})\n    result['clients']=read_json");p.write_text(s)
print('notification and byte-identical fallback patch staged')
