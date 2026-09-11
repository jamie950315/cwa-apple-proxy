from pathlib import Path
from datetime import datetime,timedelta,timezone
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID,ExtendedKeyUsageOID
import plistlib,uuid,os
base=Path('/home/jamie/cwa-weather-proxy'); p=base/'certs'; p.mkdir(exist_ok=True);os.chmod(p,0o700)
now=datetime.now(timezone.utc)
if not (p/'ca.pem').exists():
    k=rsa.generate_private_key(public_exponent=65537,key_size=3072)
    name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'CWA Weather Bridge Root')])
    cert=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(k.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(days=1)).not_valid_after(now+timedelta(days=3650)).add_extension(x509.BasicConstraints(ca=True,path_length=0),True).add_extension(x509.KeyUsage(digital_signature=True,key_encipherment=False,content_commitment=False,data_encipherment=False,key_agreement=False,key_cert_sign=True,crl_sign=True,encipher_only=False,decipher_only=False),True).add_extension(x509.NameConstraints(permitted_subtrees=[x509.DNSName('weatherkit.apple.com')],excluded_subtrees=None),True).add_extension(x509.SubjectKeyIdentifier.from_public_key(k.public_key()),False).sign(k,hashes.SHA256()))
    (p/'ca-key.pem').write_bytes(k.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()))
    (p/'ca.pem').write_bytes(cert.public_bytes(serialization.Encoding.PEM));(p/'ca.cer').write_bytes(cert.public_bytes(serialization.Encoding.DER))
    lk=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    leaf=(x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'weatherkit.apple.com')])).issuer_name(name).public_key(lk.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(days=1)).not_valid_after(now+timedelta(days=365)).add_extension(x509.BasicConstraints(ca=False,path_length=None),True).add_extension(x509.SubjectAlternativeName([x509.DNSName('weatherkit.apple.com')]),False).add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),False).add_extension(x509.KeyUsage(digital_signature=True,key_encipherment=True,content_commitment=False,data_encipherment=False,key_agreement=False,key_cert_sign=False,crl_sign=False,encipher_only=False,decipher_only=False),True).add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(k.public_key()),False).sign(k,hashes.SHA256()))
    (p/'weatherkit.pem').write_bytes(lk.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())+leaf.public_bytes(serialization.Encoding.PEM)+cert.public_bytes(serialization.Encoding.PEM))
    for f in p.iterdir():os.chmod(f,0o600)
profile={'PayloadContent':[{'PayloadType':'com.apple.security.root','PayloadVersion':1,'PayloadIdentifier':'dev.0ruka.cwa-weather.ca','PayloadUUID':str(uuid.uuid4()),'PayloadDisplayName':'CWA Weather Bridge CA','PayloadContent':(p/'ca.cer').read_bytes()}],'PayloadType':'Configuration','PayloadVersion':1,'PayloadIdentifier':'dev.0ruka.cwa-weather','PayloadUUID':str(uuid.uuid4()),'PayloadDisplayName':'CWA Weather Bridge','PayloadDescription':'Trust certificate for the personal CWA weather proxy on Pi5. DNS scope: weatherkit.apple.com. After installing, enable full trust in Certificate Trust Settings.','PayloadRemovalDisallowed':False}
(base/'data'/'CWA-Weather.mobileconfig').write_bytes(plistlib.dumps(profile))
print('PKI ready')
