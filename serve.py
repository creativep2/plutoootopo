"""Local server for Terrain Press: serves the page and proxies ESA WorldCover range reads (the bucket sends no CORS headers).

Usage: python3 serve.py [port]   then open http://localhost:8787/terrain-press.html
"""
import http.server, os, sys, urllib.error, urllib.parse, urllib.request

ALLOW = (  # only proxy these hosts
    'https://esa-worldcover.s3.eu-central-1.amazonaws.com/',
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/',
    'https://tiles.maps.eox.at/wmts/',
    'https://tile.openstreetmap.org/',
    'https://a.tile.opentopomap.org/',
)
UA = 'TerrainPress/2 (local design tool)'  # OSM tile policy requires an identifying User-Agent

class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if not self.path.startswith('/proxy?'):
            return super().do_GET()
        u = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get('u', [''])[0]
        if not u.startswith(ALLOW):
            return self.send_error(403, 'host not allowed')
        hdr = {'User-Agent': UA, **({'Range': self.headers['Range']} if self.headers['Range'] else {})}
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers=hdr), timeout=60)
        except urllib.error.HTTPError as e:
            return self.send_error(e.code)
        except OSError as e:
            return self.send_error(502, str(e))
        body = r.read()
        self.send_response(r.status)
        for k in ('Content-Type', 'Content-Range', 'Accept-Ranges'):
            if r.headers.get(k):
                self.send_header(k, r.headers[k])
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
    print(f'Terrain Press on http://localhost:{port}/terrain-press.html')
    http.server.ThreadingHTTPServer(('127.0.0.1', port), H).serve_forever()
