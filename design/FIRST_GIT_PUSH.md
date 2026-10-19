# Premier push vers un nouveau dépôt Git — Coach (préparation style premium)

## Objectif de cette préparation

Cette mission a préparé le terrain pour que Grok 4.7 puisse appliquer une refonte de style **premium, didactique et multi-proposition** sans toucher à la logique métier.

Rien n’a été modifié dans :
- app.py
- services/
- templates/*.html
- static/app.js
- migrations/
- tests/

Seuls des documents de référence et un .gitignore ont été ajoutés.

## État du dépôt après cette mission

- Dépôt Git initialisé localement (`git init`)
- `.gitignore` créé et respecté
- Dossier `design/` ajouté avec 5 documents de haute qualité
- Aucun secret, aucun .env, aucune donnée utilisateur

## Procédure recommandée pour le premier push (à exécuter par le propriétaire)

1. Créer un dépôt vide sur la plateforme de votre choix (GitHub, GitLab, Forgejo, etc.).
   - Nom suggéré : `coach` ou `coach-prototype` ou `coach-ui-foundation`
   - Ne pas initialiser avec README, .gitignore ou licence (on pushera tout).

2. Depuis ce répertoire (`/home/nicee/coach`) :

```bash
git add -A
git commit -m "chore: initial commit — fondations stables + préparation refonte style premium

- Ajout .gitignore complet
- Ajout design/ (UI_INVENTORY, STYLE_BRIEF, CURRENT_CSS_TOKENS, NON_REGRESSION_CHECKLIST, PROMPT_PACK, FIRST_GIT_PUSH)
- Aucun changement fonctionnel
- Préparation pour refonte de style didactique par Grok 4.7
- Respect strict AGENTS.md (aucun secret, aucune donnée)"

git branch -M main
git remote add origin <URL_DU_NOUVEAU_REPO>
git push -u origin main
```

3. Vérifier que le dépôt distant n’affiche ni .env ni aucun secret.

## Contenu du commit initial (ce qui doit être poussé)

Fichiers essentiels :
- Tout le code source existant (app.py, static/, templates/, services/, tests/, etc.)
- AGENTS.md, README.md
- .gitignore
- design/ (les 6 fichiers md)
- requirements.txt, migrations/, scripts/, etc.

Fichiers explicitement exclus par .gitignore :
- .env et variantes
- backups/
- *.log, __pycache__, .venv/, etc.

## Recommandations pour la suite

- Protéger la branche `main` (si possible)
- Ajouter un fichier `LICENSE` si souhaité (dans un commit séparé)
- Créer une branche `style/refonte-premium` quand on commencera la refonte réelle
- Ne jamais merger de refonte de style tant que la checklist de non-régression n’a pas été validée en navigateur

## Rappel important

Conformément à AGENTS.md :
- Chaque mission écrit un rapport `rap_seXXXX.md`
- Aucune modification fonctionnelle n’a été apportée
- Le propriétaire applique lui-même les redémarrages et migrations

---

Date : 2026-10-19
Mission : préparation fondations pour refonte UI premium par Grok 4.7
