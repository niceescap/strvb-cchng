# Inventaire

- **Étape 0 — Interpréteur** : **OBSERVÉ** — `sys.executable` est `/home/nicee/coach/.venv/bin/python`.
- **Étape 1 — Imports** : **OBSERVÉ** — `psycopg2` et `sqlalchemy` s’importent dans ce venv.
- **Garde de connexion** : **OBSERVÉ** — après `load_dotenv(Path(__file__).parent / '.env', override=True)`, `make_url(DATABASE_URL).database` correspond à `coach_proto`.
- **Connexion** : **NON OBSERVÉ** — échec avant toute requête. Message exact : `connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: Operation not permitted
	Is the server running locally and accepting connections on that socket?`. `whoami` : `nicee`.

1. **a) Colonnes de `coach_users`, `coach_activities` et `coach_artifacts` (nom, type, défaut, nullable)** — **NON OBSERVÉ** : connexion impossible; aucune requête `information_schema.columns` exécutée.
2. **b) Présence, type et défaut de `coach_users.credit_tokens`** — **NON OBSERVÉ** : connexion impossible.
3. **c) Présence de `compact_json`, `best_json` et `device_watts` dans `coach_activities`** — **NON OBSERVÉ** : connexion impossible.
4. **d) `count(*)` de `coach_users` et `coach_artifacts`** — **NON OBSERVÉ** : aucun comptage exécuté.
5. **e) Comptage des `credit_tokens` non nulles et de celles différentes de zéro** — **NON OBSERVÉ** : aucun comptage exécuté.
6. **f) Présence des tables `credit_ledger`, `model_pricing` et `coupons`** — **NON OBSERVÉ** : connexion impossible.
7. **g) Dernière migration appliquée, si la base la trace** — **NON OBSERVÉ** : impossible à vérifier sans connexion.

# Incident d'environnement

- **DATABASE_URL exportée dans `~/.bashrc` pointant vers `fu19_db`, puis retirée** — **OBSERVÉ (signalé pour cette mission)**. Cette base n’a pas été utilisée.
- **Chargement du `.env` du projet avec `override=True`** — **OBSERVÉ** dans cette exécution; la garde a confirmé la base `coach_proto` sans afficher l’URL.
- **Redémarrage de `coach-prototype` par le propriétaire** — **OBSERVÉ (signalé pour cette mission)**.
- **`/health` en HTTP 200** — **OBSERVÉ (signalé pour cette mission)**.
