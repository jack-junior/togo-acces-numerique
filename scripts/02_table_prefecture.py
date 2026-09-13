"""
Défi 1 — Togo AI Lab : construction de la table d'analyse par préfecture.
Entrées : data/*.csv, data/limites_prefectures.geojson,
          data/prefectures_population_superficie.csv (étape 1)
Sortie  : outputs/analyse_prefecture.csv — 39 préfectures x 26 indicateurs
"""
import json, math, collections
import pandas as pd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
import pyproj
from shapely.ops import transform

from _chemins import DATA, OUTPUTS
UTM31 = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:32631', always_xy=True).transform

def wkt_points(df):
    df = df.copy()
    df['lon'] = df.geometry.str.extract(r'POINT \(([-\d.]+)')[0].astype(float)
    df['lat'] = df.geometry.str.extract(r'POINT \([-\d.]+ ([-\d.]+)')[0].astype(float)
    return df

# --- socle : population, superficie, correspondance FID -> nom
base = pd.read_csv(f'{DATA}/prefectures_population_superficie.csv')

# --- points de service
tel  = wkt_points(pd.read_csv(f'{DATA}/telecom.csv'))      # = moov + togocom
moov = wkt_points(pd.read_csv(f'{DATA}/moov.csv'))
togo = wkt_points(pd.read_csv(f'{DATA}/togocom.csv'))
dc   = wkt_points(pd.read_csv(f'{DATA}/datacenters.csv'))
mm   = wkt_points(pd.read_csv(f'{DATA}/mobilemoney.csv'))
cp   = pd.read_csv(f'{DATA}/canalplus_boutiques.csv')      # lat/lon déjà séparés

# CANAL+ : affectation par jointure spatiale (pas de champ préfecture)
pref = json.load(open(f'{DATA}/limites_prefectures.geojson'))
geoms = [shape(f['geometry']) for f in pref['features']]
fids  = [f['id'] for f in pref['features']]
tree  = STRtree(geoms)
fid2name = dict(zip(base.fid, base.prefecture))

def locate(lon, lat):
    p = Point(lon, lat)
    for i in tree.query(p):
        if geoms[i].contains(p):
            return fid2name[fids[i]]
    return None

cp['prefecture'] = [locate(x, y) for x, y in zip(cp.longitude, cp.latitude)]

# --- agrégats
t = base.set_index('prefecture')
t['agences_telecom'] = tel.prefecture_nom_bdd.value_counts()
t['agences_moov']    = moov.prefecture_nom_bdd.value_counts()
t['agences_togocom'] = togo.prefecture_nom_bdd.value_counts()
t['boutiques_canalplus'] = cp.prefecture.value_counts()
t['datacenters']     = dc.prefecture_nom_bdd.value_counts()
t['momo_total']      = mm.prefecture_nom_bdd.value_counts()
for op, col in [('Moov, Togocom','momo_mixte'), ('Togocom','momo_togocom'),
                ('Moov','momo_moov'), ('Nsp','momo_nsp')]:
    t[col] = mm[mm.operateur == op].prefecture_nom_bdd.value_counts()
t = t.fillna(0)
for c in t.columns:
    if c not in ('fid','region','densite_hab_km2','superficie_km2'):
        t[c] = t[c].astype(int)

# --- indicateurs normalisés
pop = t.population_rgph5_2022
t['momo_pour_10k_hab']    = (t.momo_total / pop * 10_000).round(2)
t['agences_pour_100k_hab']= (t.agences_telecom / pop * 100_000).round(2)
t['hab_par_agence']       = (pop / t.agences_telecom.replace(0, float('nan'))).round(0)
t['hab_par_point_momo']   = (pop / t.momo_total.replace(0, float('nan'))).round(0)

# --- attendu / observé (répartition strictement proportionnelle à la population)
share = pop / pop.sum()
for src, lbl in [('momo_total','momo'), ('agences_telecom','agences')]:
    att = (share * t[src].sum())
    t[f'{lbl}_attendu']  = att.round(1)
    t[f'{lbl}_ecart']    = (t[src] - att).round(1)
    t[f'{lbl}_ratio_obs_att'] = (t[src] / att).round(3)

# --- Gini sur la répartition des points rapportée à la population
def gini(values, weights):
    d = pd.DataFrame({'v': values, 'w': weights}).sort_values('v')
    cw = d.w.cumsum() / d.w.sum()
    cv = (d.v * d.w).cumsum() / (d.v * d.w).sum()
    # aire sous la courbe de Lorenz par trapèzes
    area = ((cw.diff().fillna(cw.iloc[0])) * (cv + cv.shift(1).fillna(0)) / 2).sum()
    return round(1 - 2 * area, 4)

g_momo    = gini(t.momo_pour_10k_hab, pop)
g_agences = gini(t.agences_pour_100k_hab, pop)

t = t.reset_index()[[
    'fid','prefecture','region','population_rgph5_2022','superficie_km2','densite_hab_km2',
    'agences_telecom','agences_moov','agences_togocom','boutiques_canalplus','datacenters',
    'momo_total','momo_mixte','momo_togocom','momo_moov','momo_nsp',
    'momo_pour_10k_hab','agences_pour_100k_hab','hab_par_agence','hab_par_point_momo',
    'momo_attendu','momo_ecart','momo_ratio_obs_att',
    'agences_attendu','agences_ecart','agences_ratio_obs_att']]
t.to_csv(OUTPUTS / 'analyse_prefecture.csv', index=False, encoding='utf-8-sig')

print(f'Gini accès mobile money (pondéré population) : {g_momo}')
print(f'Gini accès agences (pondéré population)      : {g_agences}')
print(f'CANAL+ localisées : {int(t.boutiques_canalplus.sum())}/7')
print(f'Préfectures sans agence : {(t.agences_telecom == 0).sum()}')
