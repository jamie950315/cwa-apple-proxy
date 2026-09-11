from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import json
ROOT=Path('/home/jamie/cwa-weather-proxy')
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=self.path.split('?',1)[0]
        mapping={'/ca.cer':('certs/ca.cer','application/pkix-cert'),'/ca.pem':('certs/ca.pem','application/x-pem-file'),'/CWA-Weather.mobileconfig':('data/CWA-Weather.mobileconfig','application/x-apple-aspen-config')}
        if path=='/proxy.pac': data=b'function FindProxyForURL(url, host) { if (host === "weatherkit.apple.com") return "PROXY 100.78.140.101:18940"; return "DIRECT"; }';mime='application/x-ns-proxy-autoconfig'
        elif path in mapping:
            file,mime=mapping[path];data=(ROOT/file).read_bytes()
        elif path=='/healthz':data=json.dumps({'service':'cwa-weather-probe','phase':'capture'}).encode();mime='application/json'
        else:self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(data)
ThreadingHTTPServer(('100.78.140.101',18880),Handler).serve_forever()
