"""Prépare les fichiers légers consommés par le dashboard (app/data_app/)."""
import json, pandas as pd
from _chemins import DATA, OUTPUTS, DATA_APP as OUT

tab = pd.read_csv(OUTPUTS / 'analyse_prefecture.csv')
tab.to_csv(OUT/'analyse_prefecture.csv', index=False, encoding='utf-8')

# GeoJSON préfectures enrichi des noms (les polygones Géodata n'ont aucun attribut)
gj = json.load(open(f'{DATA}/limites_prefectures.geojson'))
meta = tab.set_index('fid')[['prefecture','region']].to_dict('index')
for f in gj['features']:
    m = meta.get(f['id'], {})
    f['properties'] = {'fid': f['id'], **m}
json.dump(gj, open(OUT/'prefectures.geojson','w'), ensure_ascii=False)

def pts(path, cols, **extra):
    d = pd.read_csv(f'{DATA}/{path}')
    d['lon'] = d.geometry.str.extract(r'POINT \(([-\d.]+)')[0].astype(float)
    d['lat'] = d.geometry.str.extract(r'POINT \([-\d.]+ ([-\d.]+)')[0].astype(float)
    d = d.rename(columns={'prefecture_nom_bdd':'prefecture','region_nom_bdd':'region',
                          'etab_nom':'nom','nom_localite':'localite'})
    for k,v in extra.items(): d[k]=v
    return d[cols]

C = ['nom','localite','prefecture','region','lat','lon','categorie']
infra = pd.concat([
    pts('telecom.csv',  C, categorie='Agence télécom'),
    pts('datacenters.csv', C, categorie='Data center'),
], ignore_index=True)
cp = pd.read_csv(f'{DATA}/canalplus_boutiques.csv').rename(columns={'nom':'nom','latitude':'lat','longitude':'lon'})
cp['localite']=cp.ville; cp['prefecture']='Golfe'; cp['region']='Maritime'; cp['categorie']='Boutique CANAL+'
infra = pd.concat([infra, cp[C]], ignore_index=True)
# opérateur déduit du nom de l'agence
def op(n):
    n=str(n).lower()
    if 'togocom' in n or 'togocel' in n: return 'Togocom'
    if 'moov' in n: return 'Moov'
    if 'canal' in n: return 'CANAL+'
    return 'Autre'
infra['operateur'] = [op(n) if c=='Agence télécom' else c for n,c in zip(infra.nom, infra.categorie)]
infra.to_csv(OUT/'infrastructures.csv', index=False, encoding='utf-8')

mm = pd.read_csv(f'{DATA}/mobilemoney.csv')
mm['lon'] = mm.geometry.str.extract(r'POINT \(([-\d.]+)')[0].astype(float)
mm['lat'] = mm.geometry.str.extract(r'POINT \([-\d.]+ ([-\d.]+)')[0].astype(float)
mm = mm.rename(columns={'prefecture_nom_bdd':'prefecture','region_nom_bdd':'region',
                        'commune_nom_bdd':'commune','canton_nom_bdd':'canton'})
mm[['region','prefecture','commune','canton','operateur','lat','lon']].to_csv(
    OUT/'mobile_money.csv', index=False, encoding='utf-8')

print('infrastructures:', len(infra), '| mobile money:', len(mm), '| préfectures geojson:', len(gj['features']))
