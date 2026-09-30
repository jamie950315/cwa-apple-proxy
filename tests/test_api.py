import asyncio
import json
from types import SimpleNamespace

import httpx
import pytest
import api


@pytest.mark.parametrize('outcome,visible',[('modified',True),('passthrough',False)])
def test_status_exposes_proof_only_for_the_served_modified_response(tmp_path,monkeypatch,outcome,visible):
    monkeypatch.setattr(api,'ROOT',tmp_path)
    monkeypatch.setattr(api,'store',SimpleNamespace(health=lambda:{}))
    (tmp_path/'data/proofs/candidate').mkdir(parents=True)
    (tmp_path/'certs').mkdir();(tmp_path/'certs/ca.cer').write_bytes(b'public-test-certificate')
    (tmp_path/'data/bridge-status.json').write_text(json.dumps({'last':{'status':outcome,'proof':'data/proofs/candidate'}}))
    (tmp_path/'data/proofs/candidate/report.json').write_text(json.dumps({'changes':[{'field':'temperature','after':21}]}))
    client_class=httpx.AsyncClient
    monkeypatch.setattr(api.httpx,'AsyncClient',lambda **kwargs:client_class(transport=httpx.MockTransport(lambda request:httpx.Response(200,json={'version':'0.3.2'}))))
    result=asyncio.run(api.status())
    assert ('lastProof' in result)==visible
    assert result['bridge']['last']['status']==outcome
