# Publier le dashboard en ligne (≈ 10 minutes)

Le formulaire de soumission du challenge contient un champ
**« Link to the published dashboard »**. Le remplir sécurise les critères C1
(ergonomie) et C3 (interactivité) : un jury qui doit dézipper un projet et
installer un environnement Python ne testera jamais l'interactivité.

## 1. Créer le dépôt GitHub

Le dépôt doit être **public** (Streamlit Community Cloud n'héberge gratuitement
que des dépôts publics).

```bash
cd <ce-dossier>
git init
git add .
git commit -m "Dashboard accès numérique Togo — Data Challenge Togo AI Lab"
git branch -M main
git remote add origin https://github.com/<ton-compte>/togo-acces-numerique.git
git push -u origin main
```

Si `git push` demande un mot de passe : GitHub n'accepte plus les mots de passe.
Créer un *personal access token* (Settings → Developer settings → Tokens) et
l'utiliser à la place, ou installer GitHub CLI puis `gh auth login`.

## 2. Déployer sur Streamlit Community Cloud

1. Aller sur <https://share.streamlit.io> et se connecter avec le compte GitHub.
2. **New app** → sélectionner le dépôt, la branche `main`, le fichier `app.py`.
3. **Deploy**. Le premier build prend 2 à 4 minutes (installation des
   dépendances de `requirements.txt`).
4. L'URL obtenue ressemble à
   `https://<ton-compte>-togo-acces-numerique.streamlit.app`.

## 3. Vérifier avant de coller le lien

- Ouvrir l'URL **en navigation privée** : c'est ce que verra le jury, sans ta
  session GitHub.
- Parcourir les 8 onglets, changer un filtre, vérifier que la carte se charge.
- L'app se met en veille après quelques jours d'inactivité et redémarre en ~30 s
  au premier accès. **Ouvrir l'app la veille de la clôture** pour qu'elle soit
  déjà chaude quand le jury l'ouvrira.

## 4. Renseigner la soumission

Sur `datalab.gouv.tg` → onglet du défi → **Submit my entry** :

| Champ | Contenu |
|---|---|
| Link to the published dashboard | l'URL Streamlit |
| Interactive dashboard | le `.zip` du projet |
| Analysis report | le rapport, 10 slides max (`.pptx` ou `.pdf`) |

Trois versions de soumission sont autorisées, éditables jusqu'à la clôture.
