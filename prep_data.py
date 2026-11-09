"""Build sea_d3.json (SEA ADM1 boundaries) from Natural Earth and inject into template.html.

Usage:
  # Vietnam 34 provinces (post 1 July 2025), from github.com/ThangLeQuoc/vietnamese-provinces-database
  # (derived from the official sapnhap.bando.com.vn map). Sparse-checkout json/geojson/*/*.geojson.
  curl -L -o ne_admin1.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson
  python3 prep_data.py ne_admin1.geojson template.html terrain-press.html path/to/vpd/json/geojson
"""
import json, sys, glob, os, unicodedata

C = {'VNM': 'Vietnam', 'THA': 'Thailand', 'LAO': 'Laos', 'KHM': 'Cambodia', 'MMR': 'Myanmar',
     'MYS': 'Malaysia', 'IDN': 'Indonesia', 'PHL': 'Philippines', 'SGP': 'Singapore',
     'BRN': 'Brunei', 'TLS': 'Timor-Leste'}

def ring(r):
    out = []
    for x, y in r:
        p = [round(x, 3), round(y, 3)]  # ~100 m precision
        if not out or out[-1] != p:
            out.append(p)
    return out if len(out) >= 4 else None

def area(r):
    return sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1)) / 2

def vn34(vn_dir):
    """Yield NE-shaped features for the 34 current Vietnam provinces."""
    files = sorted(glob.glob(f'{vn_dir}/*/*.geojson'))
    assert len(files) == 34, f'expected 34 Vietnam province files, got {len(files)}'
    for fn in files:
        for f in json.load(open(fn))['features']:
            p = f['properties']
            yield {'properties': {'adm0_a3': 'VNM', 'name': p['name'], 'gn_name': p['nameEn'],
                                  'type_en': 'Municipality' if p['fullName'].startswith('Thành phố') else 'Province'},
                   'geometry': f['geometry']}

def main(src, template, dst, vn_dir=None):
    d = json.load(open(src))
    feats = d['features']
    if vn_dir:  # Natural Earth still has the pre-2025 63 provinces
        feats = [f for f in feats if f['properties']['adm0_a3'] != 'VNM'] + list(vn34(vn_dir))
    res = []
    for f in feats:
        p = f['properties']
        if p['adm0_a3'] not in C:
            continue
        g = f['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        P = []
        for poly in polys:
            rr = [r for r in (ring(r) for r in poly) if r]
            # d3-geo winding: exterior clockwise (negative planar area), holes counterclockwise
            for k, r in enumerate(rr):
                a = area(r)
                if (k == 0 and a > 0) or (k > 0 and a < 0):
                    r.reverse()
            if rr:
                P.append(rr)
        res.append({'c': p['adm0_a3'], 'n': unicodedata.normalize('NFC', p['name'] or p['gn_name']), 't': p['type_en'], 'g': P})
    res.sort(key=lambda r: (C[r['c']], r['n'] or ''))
    data = json.dumps({'countries': C, 'provinces': res}, separators=(',', ':')).replace('</', '<\\/')
    colors = open(os.path.join(os.path.dirname(os.path.abspath(template)), 'brand-colors.json')).read().strip()  # Pluto token sets
    html = open(template).read().replace('__DATA__', data).replace('__COLORS__', colors)
    open(dst, 'w').write(html)
    print(f'{len(res)} regions, {len(data)/1e6:.2f} MB data -> {dst}')

if __name__ == '__main__':
    main(*sys.argv[1:5])
