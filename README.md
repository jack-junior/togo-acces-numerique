# Accès aux télécoms et aux services numériques au Togo

Diagnostic territorial, tableau de bord interactif et recommandations, produits
pour le **Data Challenge Togo AI Lab — Économie numérique, Défi 1**.

Le dépôt contient **tout** : les données brutes, la chaîne de traitement
complète, le code du tableau de bord, les tables produites, la documentation
méthodologique et le rapport.

---

## Démarrage rapide

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Git Bash
source .venv/Scripts/activate

pip install -r requirements.txt

streamlit run app.py          # lancer le tableau de bord
python scripts/run_all.py     # rejouer toute la chaîne depuis les données brutes
```

Le tableau de bord s'ouvre sur <http://localhost:8501> et fonctionne **hors
ligne** : aucune API n'est appelée à l'exécution.

Le dashboard est également publié en ligne :
<https://togo-acces-numerique.streamlit.app/>

---

## Structure du dépôt

```
.
├── app.py                 Tableau de bord Streamlit — point d'entrée
├── theme.py               Palette et styles des graphiques
├── requirements.txt
│
├── data/                  ENTRÉES — données brutes, jamais modifiées
│
├── scripts/               PIPELINE — à exécuter dans l'ordre
│   ├── _chemins.py                    chemins du projet
│   ├── 01_population_et_limites.py    population RGPH-5, superficies, noms des préfectures
│   ├── 02_table_prefecture.py         table d'analyse : taux, écarts, Gini
│   ├── 03_donnees_dashboard.py        fichiers légers pour l'application
│   ├── 04_zones_blanches_canton.py    distances et zones blanches, 396 cantons
│   └── run_all.py                     rejoue les étapes 1 à 4
│
├── outputs/               SORTIES — tables d'analyse
│   ├── analyse_prefecture.csv         39 lignes × 26 indicateurs
│   └── analyse_canton.csv             396 lignes
│
├── data_app/              SORTIES — fichiers consommés par le tableau de bord
│
├── docs/                  Documentation des sources et contrôles qualité
│   └── sources_donnees.md
│
└── rapport/               Rapport de présentation, 10 slides (PDF et PPTX)
```

---

## Le tableau de bord

Huit onglets, filtrables par région. Le diagnostic principal est présenté à
l'échelle préfectorale ; l'accès local est détaillé à l'échelle cantonale dans
l'onglet « Accès local ».

| Onglet | Contenu | Objectif du défi |
|---|---|---|
| Vue d'ensemble | Carte choroplèthe, 4 indicateurs, classement ajustable et constats clés | 2 |
| Implantations | Agences Moov/Togocom, boutiques CANAL+, data centers, agents momo | 1 |
| Inégalités d'accès | Courbe de Lorenz, indice de Gini, écart à la proportionnalité | 2 |
| Densité & accès | Croisement densité × accès, préfectures atypiques étiquetées | 3 |
| Accès local | 12 préfectures sans agence, puis les 396 cantons par distance | 4 |
| Opérateurs | Répartition mobile money, manquants « Nsp » exposés | — |
| Priorités d'action | Score de priorisation paramétrable, 5 recommandations | 5 |
| Sources & méthode | Table complète, export CSV, 6 hypothèses, limites déclarées | — |

**Les constats affichés sous chaque vue sont recalculés à partir des données
filtrées** — ce ne sont pas des textes figés. Filtrer sur une région change les
phrases.

---

## Principaux résultats

- Rapportée à la population, **Maritime n'est que troisième** (25,4 points mobile
  money / 10 000 hab.), derrière **Kara** (29,9) et **Centrale** (26,3). La moins
  bien dotée est **Plateaux** (18,8). Le classement en valeur absolue dit l'inverse.
- **12 préfectures sur 39 n'ont aucune agence télécom** : 1 446 869 habitants,
  **17,9 % de la population**. Dont Lacs (241 247 hab.) et Vo (224 411 hab.).
- À l'échelle du canton, la distance médiane à un point de service est de **2,0 km**
  mais celle à une **agence opérateur** atteint **16,2 km** (jusqu'à 63 km).
  **23 cantons sur 396** n'ont aucun point de service.
- **Gini de l'accès** : 0,309 pour le mobile money contre 0,379 pour les agences.
  Le réseau d'agents privés maille le territoire plus équitablement.
- Le déficit le plus lourd est **périurbain, pas rural** : Agoè-Nyivé, 882 695
  habitants, 761 points manquants.

---

## Les six hypothèses

Aucune n'est neutre : changer l'une d'elles change les conclusions. Elles sont
énoncées ici, dans l'onglet « Données & méthode » du tableau de bord et sur la
dernière slide du rapport — avec la même numérotation partout.

| | Hypothèse | Ce qui bougerait autrement |
|---|---|---|
| **H1** | La répartition « attendue » est proportionnelle à la population | Une norme au PIB local ou au nombre de comptes actifs donnerait un autre classement |
| **H2** | Le poids de la population dans la priorisation (α = 0,5) est un arbitrage | Réglable en direct dans le tableau de bord ; α = 0 classe au déficit brut |
| **H3** | La zone blanche est définie par l'accès au service, pas par le signal | Couches radio en accès restreint (403) ; OpenStreetMap écarté (115 mâts pour tout le pays) |
| **H4** | Le centroïde du canton représente ses habitants | Aucune population infra-préfectorale n'est publiée |
| **H5** | Les noms de préfectures et cantons sont reconstruits, pas lus | Jointure spatiale, 39/39, pureté ≥ 0,958 ; superficies à 0,18 % du chiffre officiel |
| **H6** | Ces données sont un inventaire, pas un échantillon | Aucune inférence : p-values et intervalles de confiance n'auraient pas de sens |

Les limites déclarées (double comptage évité, millésimes hétérogènes, 6,8 %
d'opérateurs non renseignés, MAUP, sophisme écologique, périmètre CANAL+,
complétude du registre) sont détaillées dans `docs/note_methodologique.md`.

---

## Sources

| Source | Usage |
|---|---|
| [Géoportail Géodata Togo](https://geodata.gouv.tg) | Agences, data centers, 19 788 agents mobile money, limites administratives |
| [INSEED — RGPH-5 (2022)](https://inseed.tg/resultats-definitifs-du-rgph-5-novembre-2022/) | Population des 39 préfectures, somme vérifiée : 8 095 498 |
| [Annuaire CANAL+ / Canal Box Togo](https://www.canalbox.tg/nos-boutiques/) | 7 boutiques géolocalisées, en substitution du jeu Géodata vide |

Extraction du **9 septembre 2026**. Le détail des identifiants de couche et des
requêtes est dans `docs/sources_donnees.md` et `scripts/00_telecharger_donnees.py`.

---

## Licence

Code sous licence MIT (`LICENSE`). Les données restent la propriété de leurs
producteurs respectifs — Géoportail Géodata Togo, INSEED.
