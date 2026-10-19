# Rapport SE1310I — relais Socket.IO des réponses agentiques

## OBSERVÉ — documentation et environnement

- OBSERVÉ : les dépendances `python-socketio 5.17.0` et `websockets 17.2` sont importables depuis le venv. Elles sont déjà déclarées dans `requirements.txt`.
- OBSERVÉ : le code Coach appelait auparavant `/api/chat/completions` en non-streaming et attendait la réponse complète avant de répondre au navigateur.
- OBSERVÉ (résultat transmis par Nicolas) : l’instance rattachée annonce `{"version":"0.12.0","deployment_id":""}`.
- OBSERVÉ : la documentation Open WebUI consultée décrit le chemin natif agentique avec `stream: true`, un `chat_id`, un id de message assistant et `session_id`. Le chat `temporary:<uuid>` permet de recevoir le flux via Socket.IO sans conserver le chat. Les événements sont enveloppés avec `chat_id`, `message_id`, `type` et `data`. La référence API indique que l’authentification HTTP accepte une clé API ou un JWT, mais le handler Socket.IO documenté valide un JWT. Sources : [Server-Side Tool Calling](https://docs.openwebui.com/reference/server-side-tool-calling/), [Backend-Controlled API Flow](https://docs.openwebui.com/reference/api-flow/), [Events](https://docs.openwebui.com/features/extensibility/plugin/development/events/) et [authentification Socket.IO dans le code Open WebUI](https://github.com/open-webui/open-webui/blob/main/backend/open_webui/socket/main.py).
- OBSERVÉ : vérification du tag officiel Open WebUI `v0.12.0` : son handler Socket.IO accepte le jeton dans `auth.token`, vérifie ce jeton, et configure le support Socket.IO avec le transport WebSocket lorsqu’il est activé. Sources : [handler Socket.IO v0.12.0](https://github.com/open-webui/open-webui/blob/v0.12.0/backend/open_webui/socket/main.py) et [routeur API v0.12.0](https://github.com/open-webui/open-webui/blob/v0.12.0/backend/open_webui/routers/openai.py).
- OBSERVÉ : sans afficher de secret, la lecture des seuls indicateurs de configuration confirme qu’aucun `OPENWEBUI_SOCKET_TOKEN` n’est présent dans le `.env` ; la clé API configurée est de type `sk-` et ne convient donc pas comme jeton Socket.IO.
- OBSERVÉ : `OPENWEBUI_TOOL_IDS` n’est pas configuré dans le `.env`. Le class tool devra être associé par défaut au modèle Open WebUI sélectionné, ou son ID devra être configuré dans `OPENWEBUI_TOOL_IDS`.
- NON OBSERVÉ : le résultat de version transmis n’a pas été obtenu par une requête indépendante depuis l’environnement de travail. Les sources taguées v0.12.0 confirment l’authentification Socket.IO et la configuration transport, mais l’examen du code de ce tag n’a pas confirmé l’ensemble des événements de chat consommés ici (deltas de réflexion, appels/résultats d’outils et formes d’artefacts). Leur réception et leur forme restent à vérifier sur l’instance attachée.
- NON OBSERVÉ : authentification réelle, réception d’événements et format des artefacts du class tool en production ; aucun appel au modèle ou au service Open WebUI n’a été lancé.

## Modifications

- `app.py` : connecter un client Socket.IO avec un JWT serveur, associer la session et le message à un chat temporaire, déclencher `/api/chat/completions` en mode natif streaming, filtrer et relayer au navigateur les événements du message concerné par SSE. Les événements de réflexion, statut, outils, fichiers, embeds et artefacts sont relayés sans implémenter de fonction métier Coach.
- `app.py` : attendre l’événement final et l’envoi de ce dernier au navigateur avant le débit. En cas d’interruption, d’erreur ou d’expiration avant cet événement, ne pas débiter. Après le commit existant, transmettre le solde relu en base par `charge_response`.
- `static/app.js` : lire le SSE progressivement, afficher la réflexion dans un panneau repliable, les statuts/appels du class tool sous forme de cases à cocher et les artefacts/fichiers/embeds au fil des événements. La jauge ne change qu’à réception de l’événement post-débit `settled`; les modèles gratuits ne la modifient pas.
- `static/style.css` : styles des panneaux de réflexion, statuts et artefacts.
- `rap_se1310i.md` : ce rapport.
- Aucun changement à `requirements.txt`, aucune migration et aucun changement à la configuration `charge_error`.

## Précondition de configuration

Le `.env` observé ne contient pas le JWT nécessaire à Socket.IO. Pour activer le flux, configurer côté service `OPENWEBUI_SOCKET_TOKEN` avec un JWT Open WebUI valide associé au même compte de service que l’API key, puis le propriétaire pourra redémarrer Coach selon sa procédure. La clé API `sk-` existante continue d’authentifier l’appel HTTP ; elle ne remplace pas ce JWT pour Socket.IO. Aucun secret n’est inclus dans ce rapport.

Le code active explicitement le mode `native` et accepte une liste d’IDs de tools via `OPENWEBUI_TOOL_IDS`. Aucun ID précis n’a été observé ; si le class tool n’est pas attaché par défaut au modèle Coach, son ID doit être configuré côté service.

## Vérifications

- OBSERVÉ : syntaxe Python (`ast.parse`) et syntaxe JavaScript (`node --check`) valides.
- OBSERVÉ : aucun test automatisé lancé, aucun échange réel avec un modèle, aucune écriture en base et aucun redémarrage/rechargement de service.
- NON OBSERVÉ : réflexion repliable, cases de fonctions/actions, artefacts créés/modifiés et jauge en conditions réelles ; ces vérifications sont réservées à Nicolas.

## Vérifications à faire par Nicolas, dans l’ordre

1. Configurer `OPENWEBUI_SOCKET_TOKEN` côté service avec un JWT valide du compte Open WebUI associé à l’API key, puis redémarrer Coach selon la procédure propriétaire.
2. Vérifier que le class tool est attaché au modèle sélectionné ; sinon renseigner son ID dans `OPENWEBUI_TOOL_IDS` et redémarrer Coach.
3. Envoyer un échange avec ce modèle et confirmer que la réflexion arrive en direct et peut être repliée/dépliée.
4. Déclencher plusieurs fonctions/actions et vérifier que chaque statut apparaît puis se coche à la fin de son exécution.
5. Faire créer et modifier un artefact ; confirmer que son panneau apparaît et se met à jour avant la fin de la réponse.
6. Pour un modèle payant, interrompre un échange avant l’événement final : vérifier l’absence de débit et de mise à jour de jauge. Puis laisser un échange se terminer : vérifier un seul débit final et que la jauge correspond au solde réellement relu en base.
7. Répéter avec un modèle gratuit : vérifier qu’aucun débit n’est journalisé et que la jauge ne bouge pas.
