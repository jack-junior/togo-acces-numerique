# Sources de données — Défi 1 Economie numérique

## 1. Jeux fournis par le défi (téléchargés — `data/`)

| Jeu | UUID | Lignes |
|---|---|---|
| Agences - Télécom | 6623b2aa-2874-462c-8e18-4f8a62d6da94 | 90 |
| Agences - Moov | 1be809a4-63c4-4aa9-bf05-b8248352facc | 28 |
| Agences - Togocom | 95780ce6-5cb3-4ce6-9595-684c97715efc | 62 |
| Agences - CANAL+ | ab3579f9-ed68-4142-8436-54c2ab7ddc95 | **0** |
| Datacenter - Établissements | 7fe2e639-b4ba-45dc-92aa-edf127e16b6b | 3 |
| Agents mobile money | 725f5fc0-4a66-49ff-9ef4-a04d004471b9 | 19 788 |

## 2. Limites administratives (trouvées sur Géodata — téléchargées)

| Jeu | UUID | Entités |
|---|---|---|
| Limites administratives - Régions | f8d02e38-1d4b-42d2-99cb-c1918316a153 | 5 |
| Limites administratives - Préféctures | 1fd2b7a3-329c-40f3-813f-7d3397d30ded | 39 |
| Limites administratives - Communes | 0d32e7d7-9ae2-4451-9df5-20e4bf9fa771 | 117 |

⚠️ Ces couches ne contiennent **aucun attribut** : uniquement un `FID` codé
(`prefectures.A01`, `regions.A`…) et la géométrie MultiPolygon (WGS84).
La correspondance code → nom a été reconstruite par **jointure spatiale** avec
les 19 788 points mobile money (qui, eux, portent les noms). Résultat :
39/39 préfectures identifiées, pureté ≥ 0,958 (37 sur 39 à 1,000).
Table de correspondance : `data/prefectures_population_superficie.csv`.

**Contrôle qualité** : la somme des superficies calculées depuis ces polygones
donne 56 681 km² contre 56 785 km² officiels — écart de 0,18 %. Les géométries
sont fiables.

## 3. Population (RGPH-5, INSEED — intégrée)
Source : INSEED Togo, *Résultats définitifs du RGPH-5 (novembre 2022)*.
Population totale 8 095 498 habitants. Les 39 préfectures reprises dans
`data/prefectures_population_superficie.csv` **somment exactement** à ce total
(contrôle effectué) et leurs noms correspondent 1:1 à ceux de Géodata.

⚠️ **Probleme de nomenclature** : le RGPH-5 publie **6 régions** (il isole
« Grand Lomé » = Golfe + Agoè-Nyivé) alors que Géodata en utilise **5**
(Maritime englobe le Grand Lomé). 

## 4. CANAL+ (substitut — le jeu officiel est vide)
Le jeu Géodata « Agences - CANAL+ » renvoie 0 enregistrement. Substitut trouvé :
l'annuaire officiel des boutiques de Canal Box / CANAL+ Togo.

```
GET https://www.canalbox.tg/wp-json/gva/v1/stores/?lang=fr
```
7 points de vente de type « CANAL+ STORE », avec coordonnées GPS exactes,
**tous à Lomé** : Dekon, Wuiti, Adidoadin, Adidogomé, Agoè, Sarakawa, Baguida.
Fichier : `data/canalplus_boutiques.csv`.

⚠️ Périmètre différent : ce sont les boutiques **en propre** de l'enseigne, pas
le réseau de revendeurs agréés. À présenter comme une source complémentaire
documentée, pas comme l'équivalent du jeu Géodata manquant.

## 5. Couverture réseau mobile — NON accessible
Géodata possède les couches pertinentes (**Tours télécoms**, + versions Moov et
Togocom ; **Réseau téléphonique enterré - Lignes - Fibre optique** ; **Bornes et
points de raccordement**), mais elles sont classées **« sur demande »** :
UUID Tours télécoms : `170c9093-5197-49ff-807f-db055444c6e4`.

**Solution retenue par défaut** : définir les zones blanches par l'**accès aux
   services** (agences et points mobile money par habitant, distance au point le
   plus proche) plutôt que par la couverture radio
