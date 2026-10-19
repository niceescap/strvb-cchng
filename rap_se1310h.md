# Rapport SE1310H — étude du streaming chat, tools et artefacts

## Résultat

Le streaming complet demandé n’est pas implémenté dans cette intervention. Le flux actuel de Coach appelle `/api/chat/completions` en HTTP non-streaming (`stream: false`) et n’a ni client Socket.IO ni canal d’événements Open WebUI dans le navigateur.

Pour Open WebUI, les tools natifs avec exécution multi-tour sont liés au chemin streaming qui porte `chat_id` et l’identifiant du message assistant ; la sortie et les événements transitent par Socket.IO. L’API HTTP directe en SSE peut streamer du texte, mais sans ce contexte elle remet les `tool_calls` au client au lieu d’exécuter le class tool. Elle ne suffit donc pas à afficher les actions réelles et les artefacts au fil de leur exécution. Références : [Server-Side Tool Calling](https://docs.openwebui.com/reference/server-side-tool-calling/) et [Events](https://docs.openwebui.com/features/extensibility/plugin/development/events/).

## Fichiers modifiés

- `rap_se1310h.md` : ce compte-rendu. Aucun fichier applicatif n’a été modifié.

## Vérifications et observations

- OBSERVÉ : la route `/api/chat` envoie actuellement `stream: false` et attend une réponse JSON complète avant de répondre au navigateur.
- OBSERVÉ : le frontend ne crée que le message assistant après cette réponse complète ; il n’a pas de rendu pour les deltas de réflexion, les étapes de tool ou les mises à jour d’artefact.
- OBSERVÉ : le venv du projet ne contient ni `socketio` ni `websockets`. La consigne `AGENTS.md` demande de s’arrêter lorsqu’un module requis manque et interdit son installation sans demande.
- NON OBSERVÉ : la version d’Open WebUI déployée et le canal d’authentification Socket.IO disponible pour Coach ; aucun appel au service n’a été effectué.
- NON OBSERVÉ : les types d’événements et le format d’artefact précis émis par le class tool installé ; aucun échange n’a été lancé.
- NON OBSERVÉ : comportement de débit en streaming ; aucun code de débit n’a été modifié.
- Aucun test lancé, aucune donnée écrite en base, aucun service redémarré.

## À vérifier pour reprendre

1. Autoriser/configurer un client Socket.IO compatible dans le venv Coach et son mode d’authentification serveur vers l’instance dédiée Open WebUI.
2. Confirmer que le class tool produit ses états d’action et ses créations/modifications d’artefact par événements Open WebUI exploitables.
3. Après implémentation, Nicolas pourra vérifier la réflexion repliable, les étapes du class tool et les artefacts en direct, puis confirmer qu’aucun débit n’a lieu avant livraison complète et que la jauge n’utilise que le solde relu après commit.
