from pathlib import Path
p=Path('/home/jamie/cwa-weather-proxy/api.py');s=p.read_text();old="store.file_get('O-A0038-003'),return_exceptions=True)";new="store.file_get('O-A0038-003'),store.get('W-C0033-001'),store.get('W-C0033-002'),return_exceptions=True)";assert old in s;s=s.replace(old,new);p.write_text(s)
