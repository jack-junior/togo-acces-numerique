"""
Rejoue toute la chaîne, des données brutes au tableau de bord.

    python scripts/run_all.py
    
"""
import runpy, sys, time, pathlib

ETAPES = [
    ('01_population_et_limites.py',  'Population RGPH-5, superficies, noms des préfectures'),
    ('02_table_prefecture.py',       'Table d’analyse par préfecture'),
    ('03_donnees_dashboard.py',      'Fichiers consommés par le dashboard'),
    ('04_zones_blanches_canton.py',  'Distances et zones blanches par canton'),
]

ICI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))

for i, (fichier, libelle) in enumerate(ETAPES, 1):
    print(f'\n\033[1m[{i}/{len(ETAPES)}] {libelle}\033[0m  ({fichier})')
    t0 = time.time()
    runpy.run_path(str(ICI / fichier), run_name='__main__')
    print(f'   terminé en {time.time()-t0:.1f} s')

print('\n\033[1mChaîne complète terminée.\033[0m  Lancer le tableau de bord :')
print('   streamlit run app.py')
