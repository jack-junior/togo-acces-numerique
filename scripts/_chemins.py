"""Chemins du projet, résolus depuis l'emplacement du script.
Permet de lancer les scripts depuis n'importe quel répertoire courant."""
import pathlib
ROOT     = pathlib.Path(__file__).resolve().parents[1]
DATA     = ROOT / 'data'        # données brutes, entrées du pipeline
OUTPUTS  = ROOT / 'outputs'     # tables d'analyse produites
DATA_APP = ROOT / 'data_app'    # fichiers légers consommés par le dashboard
for d in (OUTPUTS, DATA_APP):
    d.mkdir(exist_ok=True)
