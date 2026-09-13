"""
Objectif 4 du défi — zones blanches à l'échelle du canton (396 unités).

Faute d'accès aux couches de couverture radio du Géoportail, la
zone blanche est définie par l'ACCÈS AU SERVICE : distance entre le centroïde
du canton et le point de service le plus proche, tous services confondus.

Entrées : data/limites_cantons.geojson, data/mobilemoney.csv, data/telecom.csv,
          data/datacenters.csv, data/canalplus_boutiques.csv,
          outputs/analyse_prefecture.csv
Sortie  : app/data_app/cantons.geojson  (géométrie + indicateurs)
          outputs/analyse_canton.csv
"""
import json, collections
import numpy as np, pandas as pd, pyproj
from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely.strtree import STRtree
from scipy.spatial import cKDTree

from _chemins import DATA, OUTPUTS, DATA_APP as OUT
FWD = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:32631', always_xy=True).transform
P = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:32631', always_xy=True)

def xy(df):
    df = df.copy()
    df['lon'] = df.geometry.str.extract(r'POINT \(([-\d.]+)')[0].astype(float)
    df['lat'] = df.geometry.str.extract(r'POINT \([-\d.]+ ([-\d.]+)')[0].astype(float)
    return df

# ---- points de service (tous services confondus)
mm  = xy(pd.read_csv(f'{DATA}/mobilemoney.csv'))
tel = xy(pd.read_csv(f'{DATA}/telecom.csv'))
dc  = xy(pd.read_csv(f'{DATA}/datacenters.csv'))
cp  = pd.read_csv(f'{DATA}/canalplus_boutiques.csv').rename(
        columns={'latitude': 'lat', 'longitude': 'lon'})
pts = pd.concat([mm[['lat','lon']], tel[['lat','lon']],
                 dc[['lat','lon']], cp[['lat','lon']]], ignore_index=True)
agences = pd.concat([tel[['lat','lon']], cp[['lat','lon']]], ignore_index=True)

def proj(d):
    x, y = P.transform(d.lon.values, d.lat.values)
    return np.c_[x, y]

tree_all = cKDTree(proj(pts))
tree_ag  = cKDTree(proj(agences))

# ---- cantons
with open(f'{DATA}/limites_cantons.geojson', encoding='utf-8') as handle:
    gj = json.load(handle)
geoms = [shape(f['geometry']) for f in gj['features']]
fids  = [f['id'] for f in gj['features']]

# nommage par jointure spatiale avec les points mobile money
tree_poly = STRtree(geoms)
votes = collections.defaultdict(collections.Counter)
for lon, lat, cn, pr, rg in zip(mm.lon, mm.lat, mm.canton_nom_bdd,
                                mm.prefecture_nom_bdd, mm.region_nom_bdd):
    p = Point(lon, lat)
    for i in tree_poly.query(p):
        if geoms[i].contains(p):
            votes[fids[i]][(cn, pr, rg)] += 1
            break

rows = []
for fid, g in zip(fids, geoms):
    c = votes[fid]
    nom, pref, reg = c.most_common(1)[0][0] if c else (None, None, None)
    cen = g.centroid
    gx, gy = P.transform(cen.x, cen.y)
    d_all = tree_all.query([gx, gy])[0] / 1000
    d_ag  = tree_ag.query([gx, gy])[0] / 1000
    rows.append(dict(fid=fid, canton=nom, prefecture=pref, region=reg,
                     lat=cen.y, lon=cen.x,
                     superficie_km2=round(transform(FWD, g).area / 1e6, 1),
                     points_service=sum(c.values()),
                     dist_service_km=round(d_all, 2),
                     dist_agence_km=round(d_ag, 2)))
cn = pd.DataFrame(rows)

# préfecture déduite du code hiérarchique pour les cantons sans point
base = pd.read_csv(OUTPUTS / 'analyse_prefecture.csv')
code2pref = base.set_index(base.fid.str.replace('prefectures.', '', regex=False))
cn['code_pref'] = cn.fid.str.replace('cantons.', '', regex=False).str[:3]
cn['prefecture'] = cn.prefecture.fillna(cn.code_pref.map(code2pref.prefecture))
cn['region'] = cn.region.fillna(cn.code_pref.map(code2pref.region))
cn['canton'] = cn.canton.fillna(
    'Canton ' + cn.fid.str.replace('cantons.', '', regex=False) + ' (non nommé)')

# classement de l'éloignement
q = cn.dist_service_km
cn['classe_acces'] = pd.cut(q, [-.01, 2, 5, 10, 1e9],
                            labels=['< 2 km', '2 – 5 km', '5 – 10 km', '> 10 km'])

cn.drop(columns=['code_pref']).to_csv(OUTPUTS / 'analyse_canton.csv',
                                      index=False, encoding='utf-8-sig')

meta = cn.set_index('fid')[['canton','prefecture','region','points_service',
                            'dist_service_km','dist_agence_km']].to_dict('index')
for f in gj['features']:
    f['properties'] = {'fid': f['id'], **{k: (None if pd.isna(v) else v)
                                          for k, v in meta[f['id']].items()}}
with open(OUT / 'cantons.geojson', 'w', encoding='utf-8') as handle:
    json.dump(gj, handle, ensure_ascii=False)
cn.drop(columns=['code_pref']).to_csv(OUT / 'analyse_canton.csv',
                                      index=False, encoding='utf-8')

print(f'cantons : {len(cn)} | nommes par jointure : {(~cn.canton.str.contains("non nomme|non nommé")).sum()}')
print(f'sans aucun point de service : {(cn.points_service == 0).sum()}')
print(f'distance au service — médiane {q.median():.2f} km | p90 {q.quantile(.9):.2f} km'
      f' | max {q.max():.2f} km')
print(f'distance à une agence — médiane {cn.dist_agence_km.median():.1f} km'
      f' | max {cn.dist_agence_km.max():.1f} km')
print(cn.classe_acces.value_counts().sort_index().to_dict())
print('\nTop 10 cantons les plus éloignés :')
print(cn.nlargest(10, 'dist_service_km')[['canton','prefecture','region',
      'dist_service_km','points_service']].to_string(index=False))
