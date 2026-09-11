from pathlib import Path
R=Path('/home/jamie/cwa-weather-proxy')
p=R/'cwa_aqi.py';s=p.read_text();s=s.replace("epoch(row.get('publishtime'))", "epoch(str(row.get('publishtime','')).replace('/','-'))").replace("'previousDayComparison':'SAME'", "'previousDayComparison':'UNKNOWN'");s=s.replace("'臭氧':'OZONE'", "'臭氧':'OZONE','二氧化氮':'NO2','二氧化硫':'SO2','一氧化碳':'CO'");p.write_text(s)
p=R/'tests/mapper.test.mjs';s=p.read_text().replace("s.nowcast={start:h,end:h+3600,amount:4.2}","s.nowcast={start:now,end:now+3600,amount:4.2}");p.write_text(s)
p=R/'tests/test_additional_sources.py';s=p.read_text().replace("date=datetime.fromtimestamp(now,timezone(timedelta(hours=8))).isoformat()", "date=datetime.fromtimestamp(now,timezone(timedelta(hours=8))).strftime('%Y/%m/%d %H:%M:%S')");p.write_text(s)
p=R/'research/live_data_031.py';s=p.read_text().replace("assert s['rain'] and 'past24h' in s['rain']", "assert s['rain'] and 'past24h' in s['rain']\n            assert s.get('airQuality') and 0<=s['airQuality']['index']<=500\n            assert s.get('nwp') and len(s['nwp']['rainIntervals'])>=10");p.write_text(s)
print('AQI timestamp, unknown comparison and exact-window fixture corrected')
