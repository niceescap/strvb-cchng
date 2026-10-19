# Pack de prompt prêt à l’emploi — Refonte de style UI Premium (Coach)

Ce dossier `design/` contient tout ce dont Grok 4.7 a besoin pour exécuter une refonte de style **didactique et multi-proposition** sans toucher à la logique.

## Fichiers inclus (à fournir dans le prompt)

1. `UI_INVENTORY.md` — Inventaire complet et figé de la structure DOM, IDs critiques, classes, flux JS, composants.
2. `CURRENT_CSS_TOKENS.md` — Extraction exacte des variables et primitives actuelles.
3. `STYLE_BRIEF.md` — Brief de mission (principes, zones, livrables attendus, anti-modèles).
4. `NON_REGRESSION_CHECKLIST.md` — Checklist obligatoire de non-régression.
5. `PROMPT_PACK.md` (ce fichier) — Instructions d’exécution.

## Instructions d’exécution pour Grok 4.7 (copier-coller en tête du prompt)

```
Tu es un designer UI/UX senior spécialisé dans les interfaces didactiques premium pour applications SaaS sérieuses (sport data + IA).

Mission : refonte complète du style visuel de l’application Coach (FastAPI + Jinja + vanilla JS + un seul fichier CSS).

RÈGLES ABSOLUES (à respecter sans exception) :
- ZÉRO modification fonctionnelle.
- Tous les IDs, classes structurelles, contrats SSE, flux utilisateur listés dans UI_INVENTORY.md doivent rester 100 % compatibles.
- Tu ne touches à aucun fichier .py, aucun template HTML, aucun JS. Tu proposes uniquement du CSS (et éventuellement des classes purement additives).
- Tu dois proposer EXACTEMENT 3 directions visuelles distinctes.
- Chaque direction doit être complète : tokens + règles par composant + exemples de rendu décrits.
- Avant d’écrire le CSS, tu relis et cites les documents fournis.

Documents de référence (fournis intégralement) :
- design/UI_INVENTORY.md
- design/CURRENT_CSS_TOKENS.md
- design/STYLE_BRIEF.md
- design/NON_REGRESSION_CHECKLIST.md

Après la proposition des 3 directions, tu produiras pour la direction recommandée :
1. Un fichier CSS complet prêt à remplacer `static/style.css`
2. Un petit guide de migration (comment l’appliquer)
3. La checklist NON_REGRESSION_CHECKLIST remplie avec justification par item critique

Format de sortie attendu :
- Section “Direction 1 — Nom” + philosophie + tokens + composants
- Section “Direction 2 — Nom” ...
- Section “Direction 3 — Nom” ...
- Recommandation + CSS complet pour la meilleure
- Checklist validée
```

## Comment utiliser ce pack plus tard

1. Créer un nouveau repo (ex: coach-ui-premium ou coach-style-2026)
2. Copier le contenu du dossier `design/` + les 4 fichiers md
3. Ajouter les fichiers sources actuels en lecture seule si besoin (style.css, coach.html, app.js extraits)
4. Lancer Grok 4.7 avec le prompt pack ci-dessus + les 4 fichiers
5. Demander à Grok de produire le CSS final + les 3 propositions

## Rappel des interdits (AGENTS.md)

- Ne jamais modifier de logique
- Ne jamais toucher aux migrations, services, facturation, Strava, chat relay, etc.
- Le premier push vers le nouveau repo ne contient que la préparation (pas de style appliqué encore)

---

Date de préparation : 2026-10-19
Préparé pour : utilisation par Grok 4.7 dans une mission de refonte de style uniquement.
