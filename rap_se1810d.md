# Mission 1810D — Réflexion repliable et mémorisation des réponses LLM

## 1. État initial

OBSERVÉ (code) : `static/app.js` traite les événements SSE relayés sous `openwebui`. La réflexion est lue dans `delta.reasoning_content`, `delta.reasoning`, `delta.thinking`, dans les blocs `reasoning` et dans les événements Responses dont le type contient `reasoning` et se termine par `.delta`. Le texte final est lu depuis `delta.content`, les événements `*.output_text.delta`, `data.content`, les blocs texte de `data.output` et les blocs message terminés. `settled`, `done` et `error` sont des événements Coach séparés du flux Open WebUI.

OBSERVÉ (code) : `createLiveViews()` affiche la réflexion dans un `<details>` ouvert, puis les éléments d’outils et artefacts en direct et le texte final dans la bulle. Aucun bouton intitulé « Artefact en direct » n’était présent : le code existant affichait une zone de rendu « Artefacts en direct » pour les événements Open WebUI de fichiers/artefacts. Elle est conservée.

OBSERVÉ (code) : le serveur ne livre `settled` et `done` qu’après `[DONE]`, contrôle du contenu et règlement éventuel. Le client exige ces événements pour conserver la réponse et n’affiche les frais qu’après `settled`. L’artefact existant est stocké dans `coach_artifacts` (`user_id`, `title`, `created_at`, `category`, `markdown`, activité liée), avec lecture protégée par utilisateur via `/api/timeline` et `/api/timeline/{kind}/{item_id}`.

NON OBSERVÉ : comportement visuel en navigateur avec un fournisseur réel et les quatre harnais. Aucun flux upstream réel n’a été exécuté dans cette mission.

## 2. Diagnostic

La réflexion restait ouverte après l’apparition du texte final. Aucun chemin ne permettait de transformer la réponse courante en artefact durable : le rendu d’artefacts Open WebUI est seulement une zone de contenu transmise par le fournisseur. `created_at` et `markdown` permettent de représenter date, titre et texte d’une réponse sans nouvelle table; il manquait une clé d’idempotence et une route d’écriture authentifiée.

## 3. Modifications réalisées

- `static/app.js` : `appendAnswer()` replie une seule fois la réflexion visible au premier fragment final non vide. Les fragments vides/blancs n’entraînent pas le repli. Le `<details>` reste consultable après fermeture; en l’absence de réflexion, il demeure masqué. La réponse finale reçue continue à se mettre à jour normalement.
- `static/app.js` : à chaque bulle, capture d’un horodatage UTC au lancement de la requête et d’une clé UUID distincte. Après réception complète (`settled` + `done`) et validation du contenu, ajout en marge basse de la bulle d’un bouton « Mémoriser la réponse ». Aucun bouton n’est disponible pendant le streaming ni après erreur/incomplétude.
- `static/app.js` : le bouton désactive les clics durant l’enregistrement, envoie le contenu final livré (jamais la réflexion ni les événements SSE), puis recharge la timeline après confirmation. En cas d’erreur, un statut explicite apparaît et le bouton est réactivé.
- `static/style.css` : styles du pied de réponse et du bouton selon les contrôles existants.
- `app.py` : ajout de `POST /api/artifacts/response`, avec session `current_user`, validation du texte, de l’UUID et de l’horodatage. Le titre vient d’abord d’un titre Markdown H1, sinon du début non vide du texte avec retrait des marqueurs Markdown, sinon de « Réponse du coach ». Le texte stocké n’est pas réécrit.
- `app.py` : les artefacts nouvellement mémorisés utilisent `category='llm_response'`, `created_at` égal à la date de génération transmise et `markdown` égal au texte final exact. L’horodatage est sérialisé avec fuseau UTC lorsqu’un pilote renvoie une date naïve.
- `tests/test_demo.py` : ajout de cas couvrant persistance, contenu, titre H1, date, idempotence, titre de repli et exigence de session.

## 4. Persistance

Le modèle `Artifact` et les routes de timeline existants sont réutilisés. La migration idempotente `migrations/0005_artifact_source_key.sql` ajoute `source_key` nullable et un index unique partiel, permettant de rejouer une soumission sans doublon tout en laissant les anciens artefacts intacts. Des réponses distinctes reçoivent des UUID différents et restent mémorisables séparément. La route renvoie l’artefact enregistré; le client recharge `/api/timeline`, et le détail reste récupérable par la route existante.

NON OBSERVÉ : migration non appliquée et schéma PostgreSQL non inspecté, conformément aux consignes. Aucune donnée de production n’a été lue ou modifiée.

## 5. Tests et vérifications

- OBSERVÉ : `/home/nicee/coach/.venv/bin/python -m py_compile app.py tests/test_demo.py` s’est terminé sans erreur de compilation.
- NON VALIDÉ : les tests ciblés `test_remember_response_persists_exact_content_and_generation_time` et `test_remember_response_uses_deterministic_fallback_title_and_requires_session` ont été lancés avec le chargement dotenv neutralisé dans le processus et le SQLite défini par les tests. Le `TestClient` est resté bloqué à l’entrée de son contexte/lifespan avant le premier appel HTTP. L’exécution a été interrompue; aucun résultat de test fonctionnel n’est revendiqué.
- NON TESTÉ : interactions navigateur, repli et streaming sous quatre harnais, erreurs HTTP de mémorisation, persistance après rechargement dans un navigateur, concurrence de double soumission et absence d’écriture dans `credit_ledger` en intégration.
- NON OBSERVÉ : tests manuels et flux avec fournisseur réel; aucun service externe n’a été appelé.

## 6. Sécurité et facturation

OBSERVÉ (code) : l’écriture dépend de `current_user`; une répétition avec la même clé restitue l’artefact du même propriétaire, tandis qu’une clé appartenant à un autre compte est refusée sans révéler son contenu. Les lectures existantes filtrent aussi par propriétaire.

OBSERVÉ (code) : la route de mémorisation ne lit ni ne modifie crédit, balance, prix ou ledger. Elle ne déclenche pas `/api/chat` et ne peut donc pas provoquer de seconde facturation. Le bouton n’existe qu’après la finalisation et validation côté client du flux.

NON VALIDÉ : ces garanties n’ont pas été exercées par les tests HTTP, bloqués au démarrage du `TestClient`.

## 7. Limites restantes

La date de génération vient de l’horloge du navigateur au démarrage de la requête. Elle représente le lancement de la génération; un décalage de l’horloge client peut la rendre approximative. La session de discussion reste non persistée, selon le fonctionnement affiché par Coach; les artefacts mémorisés, eux, restent persistants.

Les scénarios SSE multiformats et les quatre harnais n’ont pas été testés en situation. Le bouton, l’affichage immédiat dans la liste et le rendu du détail nécessitent une validation navigateur après déploiement. Le démarrage bloqué du `TestClient` doit être diagnostiqué pour exécuter les tests ajoutés.

## 8. Déploiement

OBSERVÉ : aucun redémarrage, rechargement de service, déploiement, changement Nginx ou application de migration n’a été effectué.

Avant mise en service, le propriétaire doit sauvegarder `coach_proto`, appliquer `migrations/0005_artifact_source_key.sql`, puis redémarrer `coach-prototype.service` pour charger la route et les changements Python. Les fichiers statiques HTML/CSS/JS sont servis par l’application; vérifier en navigateur le chargement du bouton, les flux des harnais et la liste après enregistrement. Aucun changement de configuration Open WebUI n’est requis.
