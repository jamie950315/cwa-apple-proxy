import json
from pathlib import Path
import split_routes

def config(tmp_path,monkeypatch,domains=None):
    monkeypatch.setattr(split_routes,'ROOT',tmp_path)
    (tmp_path/'config').mkdir(exist_ok=True)
    data={'verifiedAt':1234567890,'domains':domains if domains is not None else {d:{'nameserver':'100.78.140.101','useWithExitNode':True} for d in split_routes.DNS_DOMAINS}}
    (tmp_path/'config/exit-dns-compatibility.json').write_text(json.dumps(data))

def test_all_flags_on_recorded_but_not_live(tmp_path,monkeypatch):
    config(tmp_path,monkeypatch)
    r=split_routes.exit_dns_evidence()
    assert r['allFourEnabledAtVerification'] and r['lastVerifiedAt']==1234567890
    assert r['liveFlagMonitoring'] is False

def test_one_flag_missing_fails_closed(tmp_path,monkeypatch):
    d={x:{'nameserver':'100.78.140.101','useWithExitNode':True} for x in split_routes.DNS_DOMAINS}
    d['weatherkit.apple.com']['useWithExitNode']=False
    config(tmp_path,monkeypatch,d)
    assert not split_routes.exit_dns_evidence()['allFourEnabledAtVerification']

def test_wrong_resolver_rejected(tmp_path,monkeypatch):
    d={x:{'nameserver':'1.1.1.1','useWithExitNode':True} for x in split_routes.DNS_DOMAINS}
    config(tmp_path,monkeypatch,d)
    assert not split_routes.exit_dns_evidence()['allFourEnabledAtVerification']

def test_absent_or_bad_evidence_is_not_claimed_ready(tmp_path,monkeypatch):
    monkeypatch.setattr(split_routes,'ROOT',tmp_path)
    assert not split_routes.exit_dns_evidence()['allFourEnabledAtVerification']
    (tmp_path/'config').mkdir();(tmp_path/'config/exit-dns-compatibility.json').write_text('broken')
    assert not split_routes.exit_dns_evidence()['allFourEnabledAtVerification']
