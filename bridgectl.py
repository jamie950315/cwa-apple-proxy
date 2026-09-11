"""Explicit opt-in client management. Run mutations with sudo after trusting the CA."""
import argparse,copy,ipaddress,json,os,subprocess,time
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parent
ADGUARD=Path('/opt/AdGuardHome/AdGuardHome.yaml')
MANAGED=ROOT/'config/managed-dns-rules.json'
LEGACY=[
 '! CWA Weather Bridge: Mac relay-block test',
 '||tthr.apple.com^$client=100.122.163.78',
 '||tether.edge.apple^$client=100.122.163.78',
 '! CWA Weather Bridge: Mac-only TLS DNS routing',
 '||weatherkit.apple.com^$dnsrewrite=NOERROR;A;100.78.140.101,client=100.122.163.78',
 '||weatherkit.apple.com^$dnsrewrite=NOERROR;;,dnstype=AAAA,client=100.122.163.78',
 '||weatherkit.apple.com^$dnsrewrite=NOERROR;;,dnstype=HTTPS,client=100.122.163.78',
]
def run(args):return subprocess.run(args,check=True,capture_output=True,text=True,timeout=30).stdout

def client_addresses(ip,peers):
    value=ipaddress.ip_address(ip)
    if value.version!=4 or value not in ipaddress.ip_network('100.64.0.0/10'):raise ValueError('Provide one Tailscale IPv4 address')
    peer=next((p for p in peers if ip in p.get('TailscaleIPs',[])),None)
    if peer is None:raise ValueError('Device is absent from the Pi5 Tailscale peer list')
    addresses=[]
    for addr in peer['TailscaleIPs']:
        parsed=ipaddress.ip_address(addr)
        if parsed.version==4 and str(parsed)==ip:addresses.append(str(parsed))
        elif parsed.version==6 and parsed in ipaddress.ip_network('fd7a:115c:a1e0::/48'):addresses.append(str(parsed))
    return peer,addresses

def rules_for(config,peers):
    rules=['! CWA Weather Bridge managed client rules']
    for c in config['enabled']:
        _,addresses=client_addresses(c['ipv4'],peers);selector='|'.join(addresses)
        rules.extend([
          f'||weatherkit.apple.com^$dnsrewrite=NOERROR;A;100.78.140.101,client={selector}',
          f'||weatherkit.apple.com^$dnsrewrite=NOERROR;;,dnstype=AAAA|HTTPS,client={selector}',
          f'||tthr.apple.com^$client={selector}',f'||tether.edge.apple^$client={selector}',
          f'||tether.v.aaplimg.com^$client={selector}'])
    return rules

def apply(config,peers):
    newrules=rules_for(config,peers)
    oldmanaged=json.loads(MANAGED.read_text()) if MANAGED.exists() else []
    oldclients=(ROOT/'clients.json').read_bytes()
    run(['systemctl','stop','AdGuardHome'])
    old=ADGUARD.read_bytes()
    backup=ROOT/'backups'/f'AdGuardHome-{time.time_ns()}.yaml';backup.parent.mkdir(exist_ok=True);backup.write_bytes(old);backup.chmod(0o600)
    try:
        data=yaml.safe_load(old);remove=set(LEGACY+oldmanaged)
        data['user_rules']=[r for r in data.get('user_rules',[]) if r not in remove]+newrules
        ADGUARD.write_text(yaml.safe_dump(data,allow_unicode=True,sort_keys=False))
        (ROOT/'clients.json').write_text(json.dumps(config,ensure_ascii=False,indent=2))
        run(['systemctl','start','AdGuardHome']);run(['systemctl','is-active','AdGuardHome'])
        run(['systemctl','reload','cwa-weather-routing'])
        MANAGED.write_text(json.dumps(newrules,ensure_ascii=False,indent=2))
    except Exception:
        run(['systemctl','stop','AdGuardHome']);ADGUARD.write_bytes(old);(ROOT/'clients.json').write_bytes(oldclients)
        subprocess.run(['systemctl','start','AdGuardHome'],check=False)
        subprocess.run(['systemctl','reload','cwa-weather-routing'],check=False)
        raise
    print(json.dumps({'enabled':config['enabled'],'dnsRules':len(newrules),'backup':str(backup)},ensure_ascii=False,indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['status','apply','enable','disable','disable-all'])
    p.add_argument('ipv4',nargs='?');p.add_argument('--confirm-certificate-trusted',action='store_true');p.add_argument('--dry-run',action='store_true')
    args=p.parse_args();config=json.loads((ROOT/'clients.json').read_text())
    if args.action=='status':print(json.dumps(config,ensure_ascii=False,indent=2));return
    if not args.dry_run and os.geteuid()!=0:p.error('Use sudo for network configuration changes')
    status=json.loads(run(['tailscale','status','--json']));peers=list(status.get('Peer',{}).values())
    if args.action in ['enable','disable'] and not args.ipv4:p.error('IPv4 address is required')
    if args.action=='enable':
        if not args.confirm_certificate_trusted:p.error('Install and fully trust the CA, then provide --confirm-certificate-trusted')
        peer,_=client_addresses(args.ipv4,peers)
        if not any(c['ipv4']==args.ipv4 for c in config['enabled']):config['enabled'].append({'name':peer.get('HostName',args.ipv4),'ipv4':args.ipv4})
        config['pending']=[c for c in config.get('pending',[]) if c['ipv4']!=args.ipv4]
    if args.action=='disable':config['enabled']=[c for c in config['enabled'] if c['ipv4']!=args.ipv4]
    if args.action=='disable-all':config['enabled']=[]
    if args.dry_run:print(json.dumps({'clients':config,'rules':rules_for(config,peers)},ensure_ascii=False,indent=2));return
    apply(config,peers)
if __name__=='__main__':main()
