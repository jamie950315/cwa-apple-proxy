import json
from pathlib import Path
from types import SimpleNamespace

import pytest
import bridgectl


def fixture(tmp_path,monkeypatch):
    (tmp_path/'config').mkdir()
    clients=tmp_path/'clients.json';clients.write_text(json.dumps({'enabled':[],'pending':[]}))
    adguard=tmp_path/'adguard.yaml';adguard.write_text('user_rules: [unrelated]\n')
    managed=tmp_path/'config/managed-dns-rules.json';managed.write_text('[]')
    monkeypatch.setattr(bridgectl,'ROOT',tmp_path)
    monkeypatch.setattr(bridgectl,'ADGUARD',adguard)
    monkeypatch.setattr(bridgectl,'MANAGED',managed)
    commands=[]
    monkeypatch.setattr(bridgectl,'run',lambda args:commands.append(args) or 'active')
    monkeypatch.setattr(bridgectl.subprocess,'run',lambda args,**kwargs:commands.append(args) or SimpleNamespace(returncode=0))
    return adguard,managed,commands


@pytest.mark.parametrize('failure',['read','backup'])
def test_read_or_backup_failure_restarts_adguard(tmp_path,monkeypatch,failure):
    adguard,managed,commands=fixture(tmp_path,monkeypatch)
    read=Path.read_bytes;write=Path.write_bytes
    def failing_read(path):
        if path==adguard:raise OSError('Read failed')
        return read(path)
    def failing_write(path,data):
        if path.parent.name=='backups':raise OSError('Backup failed')
        return write(path,data)
    monkeypatch.setattr(Path,'read_bytes',failing_read if failure=='read' else read)
    monkeypatch.setattr(Path,'write_bytes',failing_write if failure=='backup' else write)
    with pytest.raises(OSError):bridgectl.apply({'enabled':[],'pending':[]},[])
    assert ['systemctl','start','AdGuardHome'] in commands
    assert adguard.read_text()=='user_rules: [unrelated]\n' and managed.read_text()=='[]'


def test_partial_managed_metadata_failure_restores_all_config(tmp_path,monkeypatch):
    adguard,managed,commands=fixture(tmp_path,monkeypatch)
    clients_before=(tmp_path/'clients.json').read_bytes();write=Path.write_text
    def failing_write(path,data,*args,**kwargs):
        if path==managed:
            write(path,'partial');raise OSError('Metadata failed')
        return write(path,data,*args,**kwargs)
    monkeypatch.setattr(Path,'write_text',failing_write)
    with pytest.raises(OSError):bridgectl.apply({'enabled':[],'pending':[{'name':'test'}]},[])
    assert managed.read_text()=='[]'
    assert adguard.read_text()=='user_rules: [unrelated]\n'
    assert (tmp_path/'clients.json').read_bytes()==clients_before
