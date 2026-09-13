"""
ÉTAPE 1 — construire la table de référence des 39 préfectures.

Trois problèmes résolus ici :

1. Les polygones de Géodata sont livrés SANS AUCUN ATTRIBUT : seulement un code
   (« prefectures.A01 ») et une géométrie. La correspondance code -> nom est
   reconstruite par JOINTURE SPATIALE : chacun des 19 788 points mobile money
   porte le nom de sa préfecture ; on regarde dans quel polygone il tombe et on
   retient le nom majoritaire.

2. Le défi ne fournit aucune donnée de population. Les effectifs proviennent de
   l'INSEED, résultats définitifs du RGPH-5 de novembre 2022. Ils sont saisis
   explicitement ci-dessous pour être auditables, et leur somme est VÉRIFIÉE
   contre le total national publié (8 095 498).

3. Les superficies sont calculées depuis les polygones, en projection métrique
   UTM 31N. Contrôle : le total doit approcher les 56 785 km² officiels.

Sortie : data/prefectures_population_superficie.csv
"""
import collections
import pandas as pd
import pyproj
from shapely.geometry import shape, Point
from shapely.ops import transform
from shapely.strtree import STRtree
import json
from _chemins import DATA

TOTAL_NATIONAL_RGPH5 = 8_095_498
SUPERFICIE_OFFICIELLE_KM2 = 56_785

# INSEED — RGPH-5, résultats définitifs (novembre 2022), population par préfecture
POPULATION = {
    'Golfe': 1_305_681, 'Agoè-Nyivé': 882_695, 'Zio': 500_032, 'Yoto': 174_851,
    'Bas-Mono': 94_860, 'Lacs': 241_247, 'Vo': 224_411, 'Avé': 111_214,
    'Ogou': 253_467, 'Moyen-Mono': 90_505, 'Haho': 305_096, 'Agou': 85_793,
    'Kloto': 145_986, 'Kpélé': 80_939, 'Danyi': 40_240, 'Wawa': 101_300,
    'Akébou': 73_830, 'Amou': 114_172, 'Anié': 180_158, 'Est-Mono': 164_460,
    'Tchaoudjo': 240_360, 'Tchamba': 200_585, 'Blitta': 163_272,
    'Sotouboua': 138_864, 'Mô': 52_448, 'Kozah': 283_738, 'Assoli': 66_394,
    'Bassar': 152_065, 'Dankpen': 185_662, 'Kéran': 128_687,
    'Doufelgou': 84_767, 'Binah': 84_199, 'Tône': 388_775, 'Cinkassé': 128_959,
    'Kpendjal-Ouest': 123_330, 'Kpendjal': 88_365, 'Oti-Sud': 150_376,
    'Oti': 124_848, 'Tandjoaré': 138_867,
}

UTM31 = pyproj.Transformer.from_crs('EPSG:4326', 'EPSG:32631', always_xy=True).transform


def main():
    assert sum(POPULATION.values()) == TOTAL_NATIONAL_RGPH5, (
        'La somme des préfectures ne correspond pas au total national du RGPH-5.')
    print(f'Population : {len(POPULATION)} préfectures, somme vérifiée '
          f'= {TOTAL_NATIONAL_RGPH5:,}'.replace(',', ' '))

    gj = json.load(open(DATA / 'limites_prefectures.geojson'))
    geoms = [shape(f['geometry']) for f in gj['features']]
    fids = [f['id'] for f in gj['features']]
    tree = STRtree(geoms)

    mm = pd.read_csv(DATA / 'mobilemoney.csv')
    mm['lon'] = mm.geometry.str.extract(r'POINT \(([-\d.]+)')[0].astype(float)
    mm['lat'] = mm.geometry.str.extract(r'POINT \([-\d.]+ ([-\d.]+)')[0].astype(float)

    votes = collections.defaultdict(collections.Counter)
    for lon, lat, pref, reg in zip(mm.lon, mm.lat,
                                   mm.prefecture_nom_bdd, mm.region_nom_bdd):
        p = Point(lon, lat)
        for i in tree.query(p):
            if geoms[i].contains(p):
                votes[fids[i]][(pref, reg)] += 1
                break

    lignes = []
    for fid, g in zip(fids, geoms):
        c = votes[fid]
        if not c:
            raise RuntimeError(f'Aucun point dans {fid} : nom non reconstructible.')
        (nom, reg), n = c.most_common(1)[0]
        lignes.append(dict(fid=fid, prefecture=nom, region=reg,
                           purete=round(n / sum(c.values()), 3),
                           superficie_km2=round(transform(UTM31, g).area / 1e6, 1)))
    t = pd.DataFrame(lignes)

    manquants = set(t.prefecture) ^ set(POPULATION)
    assert not manquants, f'Noms non appariés : {manquants}'
    print(f'Jointure spatiale : {len(t)}/{len(POPULATION)} préfectures identifiées, '
          f'pureté minimale {t.purete.min():.3f}')

    t['population_rgph5_2022'] = t.prefecture.map(POPULATION)
    t['densite_hab_km2'] = (t.population_rgph5_2022 / t.superficie_km2).round(1)

    total = t.superficie_km2.sum()
    ecart = abs(total - SUPERFICIE_OFFICIELLE_KM2) / SUPERFICIE_OFFICIELLE_KM2
    print(f'Superficies : {total:,.0f} km² calculés contre '
          f'{SUPERFICIE_OFFICIELLE_KM2:,} officiels — écart {ecart*100:.2f} %'
          .replace(',', ' '))
    assert ecart < 0.02, 'Écart de superficie trop important : géométries suspectes.'

    cible = DATA / 'prefectures_population_superficie.csv'
    t[['fid', 'prefecture', 'region', 'superficie_km2',
       'population_rgph5_2022', 'densite_hab_km2']].to_csv(
        cible, index=False, encoding='utf-8-sig')
    print(f'-> {cible.relative_to(DATA.parent)}')


if __name__ == '__main__':
    main()
