# AGENTS.md — Coach

## Projet
Application FastAPI dans /home/nicee/coach. Service systemd coach-prototype.service sur 127.0.0.1:2025, WorkingDirectory=/home/nicee/coach. Base PostgreSQL coach_proto, connexion via DATABASE_URL dans .env. Service OAuth sur 127.0.0.1:2024.
- Le .env du projet fait foi : load_dotenv(..., override=True). Ne jamais se fier à DATABASE_URL de l'environnement du shell.

## Interpréteur
- Toujours utiliser /home/nicee/coach/.venv/bin/python, en chemin absolu.
- Ne jamais utiliser python3 ou pip du système. Ne jamais installer de paquet système, ni avec --break-system-packages.
- Si un module manque dans le venv, le signaler et s'arrêter. Ne pas l'installer sans demande.

## Tests
- Tests existants : .venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
- Un seul fichier : .venv/bin/python -m unittest tests/test_xxx.py -v
- tests/test_openwebui_models.py utilise pytest : .venv/bin/python -m pytest -q tests/test_openwebui_models.py
- Ne lancer que les tests demandés par la mission.

## Interdits
- Ne jamais redémarrer ni recharger un service systemd. Le propriétaire le fait lui-même.
- Ne jamais afficher le contenu de .env, ni aucune valeur de variable d'environnement, clé, token, secret ou mot de passe.
- Ne jamais afficher de lignes de données utilisateur (coach_users, tokens Strava, activités).
- Ne jamais toucher à l'instance Open WebUI du port 8080 (service systemd). L'instance dédiée à Coach est le conteneur RiveraiOI8070, port 8070.
- Ne pas modifier la configuration Nginx, ni déployer.

## Base de données
- Le pilote est psycopg2 (DATABASE_URL=postgresql+psycopg2). Ne pas tester ni utiliser psycopg (v3).
- Lire la connexion depuis DATABASE_URL, jamais en dur.
- Les migrations sont des fichiers SQL numérotés dans migrations/. Ne jamais modifier une migration déjà appliquée : en créer une nouvelle avec le numéro suivant.
- Écrire les migrations idempotentes (IF NOT EXISTS, ADD COLUMN IF NOT EXISTS).
- Ne pas appliquer de migration. Le propriétaire l'applique après une sauvegarde pg_dump.
- Pour les inventaires : seulement information_schema et count(*). Aucune donnée affichée.

## Crédits et argent
- Les montants sont des entiers en micro-dollars. Aucun float pour l'argent.
- Toute modification de solde passe par une ligne ajoutée dans credit_ledger. Ne jamais modifier un solde sans écriture de journal.
- Les codes de coupon ne sont jamais stockés en clair, seulement leur HMAC.

## Rapports
- Chaque mission écrit son rapport dans ~/coach/rap_seXXXX.md.
- Pour chaque fait d'environnement, marquer OBSERVÉ (avec le résultat) ou NON OBSERVÉ (avec la raison). Ne jamais remplir un point observable à partir du code.
- Rédiger en français.

## Périmètre
- Une mission, un périmètre. Ne pas élargir sans demande écrite.
- Aucun modèle de chat n'est branché tant que le module crédits n'est pas validé.
