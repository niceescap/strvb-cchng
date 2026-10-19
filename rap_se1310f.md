# Mission SE1310F — débit selon le coût réel

## Principe et formules

- Les coûts sont convertis avec `Decimal(str(valeur))`; les débits restent des entiers en micro-dollars et sont arrondis au supérieur.
- Coût fournisseur : `ceil(usage.cost × 10 × 1 000 000)`.
- Repli aux tarifs : `ceil((prompt_tokens × P_in + completion_tokens × P_out) × 10 / 1 000 000)`.
- Pré-contrôle : `ceil((caractères du message × P_in + 2048 × P_out) × 10 / 1 000 000)`. Le plafond de sortie est fixé à 2048 tokens côté serveur.
- Une absence de tarif actif empêche l'appel d'un modèle payant ; le modèle gratuit doit être explicitement configuré par `OPENWEBUI_FREE_MODELS`. Ainsi, une réponse payante n'est jamais envoyée sans borne de pré-contrôle calculable.
- Le débit est tenté après validation d'un contenu non vide et d'une fin autre que `length`. Le solde et le journal sont mis à jour dans une transaction ; si le solde a baissé depuis le pré-contrôle, le débit partiel consomme le solde disponible sans passer sous zéro.
- La route est un proxy non-streaming OpenAI-compatible vers Open WebUI. Le journal serveur ne contient aucun contenu de conversation.

## Fichiers modifiés

- `app.py` : fonctions de calcul au plafond décimal, pré-contrôle, validation de réponse, proxy `/api/chat`, puis écriture atomique du débit et du journal. `model_pricing.active` conditionne l'accès payant ; aucune activation de modèle n'a été effectuée.
- `static/app.js` : envoi du message à la route et ajout de la ligne discrète « Coût : X $ · Solde : Y $ » sous une réponse livrée.
- `tests/test_metering.py` : tests unitaires sans réseau et deux tests de cycle transactionnel PostgreSQL avec rollback externe et garde sur `coach_proto`.

## Vérifications et faits d'environnement

- **OBSERVÉ** — interpréteur utilisé : `/home/nicee/coach/.venv/bin/python`.
- **OBSERVÉ** — commande `/home/nicee/coach/.venv/bin/python -m unittest tests/test_metering.py -v` : 6 tests unitaires réussis ; le groupe PostgreSQL est ignoré à `setUpClass`, car la connexion a échoué (`OperationalError`).
- **NON OBSERVÉ** — débit exact et cohérence du journal sur PostgreSQL : connexion `coach_proto` indisponible ; aucun cycle de test PostgreSQL n'a été exécuté.
- **NON OBSERVÉ** — état effectif des tarifs et activation de `coach-par-claude`, `coach-par-gpt` et `coach-par-kimi` : impossible de lire la base. Aucun modèle n'a été activé ni réglage de base modifié pendant cette mission. Le code exige `active = true` pour chaque modèle payant.
- **NON OBSERVÉ** — comportement auprès du fournisseur : aucun appel réseau réel n'a été effectué.
- **OBSERVÉ** — `git diff --check` n'a pas pu être exécuté utilement : ce répertoire ne contient pas de dépôt Git exploitable (`.git` n'est pas un dépôt).

## Limites et décisions

- Deux appels simultanés peuvent passer le pré-contrôle ensemble ; l'écriture finale reste protégée contre un solde négatif et facture partiellement si nécessaire.
- Les vérifications du chemin d'erreur fournisseur sont unitaires sur le validateur de réponse ; aucun appel réel au fournisseur n'a été fait.
- Aucune migration, écriture SQL applicative, activation de modèle, modification de route coupon, redémarrage ou déploiement n'a été effectué.

## Actions du propriétaire

1. Redémarrer `coach-prototype.service`.
2. Après validation, passer `enabled` à `True` pour un seul modèle (dans le schéma disponible ici, le champ lu par la route est `model_pricing.active`).
3. Tester avec un message court.

## SE1310F-bis — historique multi-tours

### Contrat et plafonds

- `/api/chat` reçoit `messages`, une liste de `{role, content}` ; seuls `user` et `assistant` sont admis, le dernier message doit être `user`.
- Maximum 20 messages, 4 000 caractères par contenu et 30 000 caractères cumulés. Toute violation renvoie une erreur 400 générique avant l'appel HTTP.
- Le pré-contrôle additionne les caractères de tous les messages et conserve la borne de sortie de 2048 tokens. Les formules de débit après réponse n'ont pas changé.
- Le fournisseur reçoit la liste validée dans son ordre d'origine avec `max_tokens: 2048` et `stream: false`.
- Le navigateur garde les tours uniquement dans une variable en mémoire de page. Avant envoi, il écarte les plus anciens messages jusqu'à respecter 30 000 caractères, en gardant le dernier message utilisateur. Rien n'est persisté.

### Fichiers modifiés

- `app.py` : validation de l'historique avant tout appel, calcul du pré-contrôle sur tous ses contenus et transmission du payload complet.
- `static/app.js` : accumulation des messages utilisateur et assistant en mémoire et coupe de l'historique avant dépassement du plafond.
- `tests/test_metering.py` : tests ordre du payload, hausse du plafond, refus des messages system, dépassements des limites et dernier rôle incorrect. La classe et les tests PostgreSQL existants sont inchangés.

### Vérifications

- **OBSERVÉ** — `/home/nicee/coach/.venv/bin/python -m unittest tests/test_metering.py -v` : 9 tests unitaires réussis.
- **NON OBSERVÉ** — tests PostgreSQL de débit : ignorés à `setUpClass` car la connexion à `coach_proto` échoue (`OperationalError`). Ils n'ont pas été lancés et aucune écriture DB n'a eu lieu.
- **OBSERVÉ** — aucun appel fournisseur réel n'a été effectué ; les tests de route utilisent un transport HTTP simulé.
- **OBSERVÉ** — aucun redémarrage de service ni activation de modèle payant n'a eu lieu.

### Action du propriétaire

Redémarrer `coach-prototype.service`, puis tester une conversation de trois tours avec Haiku, activé temporairement pour ce test.

## SE1310H — correction du débit payant (`charge_error`)

### Diagnostic

- **Cause confirmée par inspection du flux** : la route appelait `db.rollback()`, puis relisait `user.id` dans l'appel de débit et dans les journaux. Le rollback expire les objets ORM ; accéder ensuite à l'attribut peut déclencher un rechargement et rouvrir une transaction. `charge_response` utilisait alors `with db.begin()`, incompatible avec une transaction déjà démarrée sur la session.
- **NON OBSERVÉ** — reproduction PostgreSQL : le test de régression reproduisant la séquence ORM `get` → capture de l'identifiant → `rollback` → `charge_response` a été ajouté, mais n'a pas été exécuté conformément à la consigne de mission. La cause n'est donc pas reproduite dynamiquement dans cette exécution.

### Corrections

- `app.py` : capture de `uid` avant tout rollback et utilisation de cette valeur simple par la suite. `charge_response` exécute maintenant ses requêtes, puis commit en cas de succès ou rollback sur exception, sans `db.begin()`. Le chemin `SQLAlchemyError` journalise via `logger.exception` la classe et le message de l'exception, tout en gardant la réponse 500 « Débit impossible » ; aucun contenu de conversation n'est journalisé.
- `tests/test_metering.py` : le test PostgreSQL de débit exact charge l'utilisateur avec l'ORM, capture son identifiant, appelle `session.rollback()`, puis vérifie le débit et le journal. Le test de débit partiel existant est inchangé.
- Les formules de débit, le débit partiel, le pré-contrôle, la route gratuite et le front n'ont pas été modifiés. Aucune migration, activation de modèle ou action de service n'a eu lieu.

### Vérifications

- **OBSERVÉ** — `/home/nicee/coach/.venv/bin/python -m unittest tests.test_metering.MeteringUnitTests -v` : 9 tests unitaires réussis.
- **NON OBSERVÉ** — test PostgreSQL de régression et test de débit partiel : non exécutés, conformément à la consigne ; ils nécessitent la connexion `coach_proto` et leur résultat ne peut pas être confirmé ici.
- **OBSERVÉ** — aucun service redémarré et aucun modèle payant activé.

### Action du propriétaire

Lancer `/home/nicee/coach/.venv/bin/python -m unittest tests/test_metering.py -v` dans l'environnement où `coach_proto` est accessible. Aucun redémarrage n'est demandé par cette mission.

## SE1310G — affichage du chat (front uniquement)

### Textes remplacés

- L'en-tête et le titre de page affichent « Coach », sans badge de démonstration.
- Le message d'accueil est statique et neutre : « Comment puis-je vous aider aujourd’hui ? ».
- Les mentions de réponses simulées, de prévisualisation et du mode démo ont été supprimées des fichiers front concernés.
- Le pied de conversation indique : « Conversation non sauvegardée : elle disparaît au rechargement de la page. ».

### Réponses, erreurs et coûts

- Chaque requête capture le nom affiché et le `model_id` sélectionnés au moment de l'envoi. Le nom est conservé dans l'élément de conversation et reste celui de la réponse même si le sélecteur change ensuite.
- Une bulle assistant avec « … » apparaît pendant l'attente. Elle est remplacée par le texte reçu, ou « Pas de réponse. » si le contenu est vide. Le texte est inséré avec `textContent` et conserve les retours à la ligne.
- Les erreurs HTTP 400, 402, 403, 500, 502 et 503 sont affichées sur une ligne système séparée, avec le détail serveur s'il existe et un texte de repli adapté sinon. La bulle en attente est retirée et l'erreur n'est pas ajoutée à l'historique.
- Sous une réponse non vide livrée, les modèles `coach-gratuit-1` et `coach-gratuit-2` affichent « Gratuit · Solde : X $ » ; les autres affichent « Coût : Y $ · Solde : X $ ». Les entiers micro-dollar sont formatés avec `BigInt`, une virgule décimale et la précision demandée.

### Fichiers et vérification

- `templates/coach.html` : titre, accueil, pied de conversation et textes de contexte mis à jour.
- `static/app.js` : affichage du modèle, indicateur d'attente, lignes d'erreur, coût et formatage des montants.
- **OBSERVÉ** — `node --check static/app.js` : code de sortie 0.
- **NON OBSERVÉ** — rendu navigateur : aucun navigateur n'a été lancé.
- Aucun test automatisé supplémentaire, aucun appel réseau ajouté, aucun changement serveur ou de facturation, aucun redémarrage ni activation de modèle.
