# Réparation /api/chat en SSE HTTP direct — 2026-10-18

## 1. État avant modification

- **OBSERVÉ — signature et structure** : `chat(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db))` était décorée par `POST /api/chat` (avant modification, lignes 619–620). Le `relay()` imbriqué commençait à la ligne 748 et était retourné dans un `StreamingResponse` (lignes 917–920).
- **OBSERVÉ — Socket.IO** : `import socketio` était présent ligne 31. `chat()` construisait un `socketio.AsyncClient`, une `asyncio.Queue`, un handler `@sio.on('events')`, appelait `sio.connect()` puis `sio.emit('user-join', ...)` (lignes 681–695 avant modification). Le `finally` appelait `sio.disconnect()` (ligne 914).
- **OBSERVÉ — rooms** : `user-join` était présent; aucun événement ou appel littéral `events:chat`/`chat:join` n’était présent. Le code attendait les événements reçus sur `events` puis filtrait par identifiants.
- **OBSERVÉ — corps upstream** : le corps contenait `chat_id`, `id`, `user_message` et les sous-champs de ce dernier (lignes 701–727 avant modification). `user_message_id` était produit ligne 703. `session_id` n’était pas présent.
- **OBSERVÉ — injection système déjà présente** : contrairement à l’hypothèse de départ, l’ancienne version construisait déjà `context_message` avec l’identifiant de discussion et le JSON de `build_context`, puis l’insérait en tête de `messages` (lignes 635–655 avant modification). La refonte conserve ce principe, tout en renforçant la validation et l’association utilisateur.
- **OBSERVÉ — flux SSE navigateur** : `static/app.js` envoie déjà `discussion_id` dans le POST (ligne 78). Il traite `openwebui`, `settled`, `error` et `done` (lignes 96–104); `ready` est simplement ignoré et ne bloque pas le lecteur. `renderOpenWebUIEvent()` (ligne 336) accepte `type: 'chat:completion'` et lit `data.choices[].delta.content` (lignes 339, 356–360).

## 2. Changements appliqués dans app.py

- **Avant, lignes 31 et 681–695; après, ligne 32** : suppression de l’import et de la connexion Socket.IO, de sa queue et du handler `events`/`user-join`.
- **Avant, lignes 701–732; après, lignes 684–692** : le corps upstream est minimal : `model`, `messages`, `stream`, `max_tokens`, et `tool_ids` seulement si configurés. Il ne contient plus de `chat_id`, `id`, `session_id`, `user_message` ni `user_message_id`.
- **Avant, ligne 748; après, ligne 734** : `relay()` utilise `httpx.AsyncClient.stream('POST', .../api/chat/completions)` (lignes 738–743), avec `Authorization: Bearer ...` et le payload minimal.
- **Avant, lignes 619–920; après, lignes 620–853** : signature publique et dépendances FastAPI conservées. Allowlist (lignes 656–658), tarification et contrôle du solde (lignes 661–678), `charge_response()` et insertion du journal de crédit conservés; la fonction de débit est appelée aux lignes 810–815.
- **Après, lignes 633–646** : `discussion_id` doit correspondre à `temporary:<UUID>` (46 caractères maximum). Le bridge est chargé via `ChatContext`; s’il n’existe pas encore, il est créé et lié à l’utilisateur authentifié. Un identifiant déjà associé à un autre utilisateur est rejeté par 404. Une course à la création relit l’enregistrement après `IntegrityError`, puis applique le même contrôle propriétaire.
- **Après, lignes 701–732** : ajout de `iter_sse_data()`, qui décode UTF-8 de façon incrémentale, accumule les fragments de lignes, traite les séparateurs SSE et assemble les lignes `data:` d’un même événement.
- **Après, lignes 748–776** : analyse JSON des chunks, agrégation de tous les `choices[].delta.content`, récupération de `finish_reason` et fusion de `usage`; arrêt sur `data: [DONE]`. EOF sans `[DONE]`, JSON incorrect et chunks invalides déclenchent une erreur SSE côté Coach.
- **Après, lignes 779–780 et 830–853** : le relais vérifie si le navigateur s’est déconnecté avant le règlement; dans ce cas, ne facture pas. Les timeouts, erreurs HTTP/réseau upstream, JSON/UTF-8 invalide et erreurs inattendues sont journalisés et produisent un événement `error`.
- **OBSERVÉ — interpréteur local** : `/home/nicee/coach/.venv/bin/python --version` indique Python 3.12.3; `asyncio.timeout()` utilisé à la ligne 748 est disponible dans cette version.
- **NON OBSERVÉ — numérotation exacte avant** : les numéros avant sont ceux relevés dans le fichier avant patch; le déplacement d’une ligne dû à la suppression de l’import peut décaler les lignes qui suivent.

## 3. Changements appliqués dans static/app.js

Aucun changement nécessaire. Le front envoie `discussion_id` à la ligne 78 et son lecteur accepte le contrat SSE maintenu. L’événement `ready` n’est pas traité explicitement, mais il est décodé puis ignoré; la lecture continue. L’enveloppe Coach `{type: 'chat:completion', data: <chunk OpenAI>}` est consommée par `renderOpenWebUIEvent()` et ses choix delta sont rendus.

## 4. Message système injecté

Le texte exact envoyé en tête de `messages` est :

```text
Identifiant de discussion Coach : <discussion_id>
Contexte d’analyse sélectionné par l’athlète (JSON) :
<JSON compact du bridge>
```

Le préfixe sur une seule ligne est toujours présent; les deux lignes suivantes et le JSON compact sont ajoutés si `build_context()` renvoie un payload. Les lignes 653–654 l’insèrent avant les messages utilisateur et ajoutent `len(context_message)` à `input_characters`. Cette longueur entre dans `maximum_debit_micro_usd()` aux lignes 668–670; le contexte ne peut donc pas contourner le pré-débit maximal.

## 5. Format exact du payload upstream envoyé à Open WebUI

Exemple anonymisé; `tool_ids` n’apparaît que si `OPENWEBUI_TOOL_IDS` est configuré :

```json
{
  "model": "<model_id autorisé>",
  "messages": [
    {"role": "system", "content": "Identifiant de discussion Coach : temporary:<UUID>\nContexte d’analyse sélectionné par l’athlète (JSON) :\n{...}"},
    {"role": "user", "content": "<message>"}
  ],
  "stream": true,
  "max_tokens": 2048,
  "tool_ids": ["<tool_id configuré>"]
}
```

Les valeurs non applicables sont omises; en particulier `tool_ids` est absent si la configuration est vide. Aucun identifiant de conversation Open WebUI n’est transmis.

## 6. Parsing SSE côté Coach

`iter_sse_data()` conserve les octets partiels avec un décodeur UTF-8 incrémental et un buffer texte; il ne traite une ligne qu’après réception de `\n`, enlève le `\r` de CRLF, collecte les lignes `data:` et émet leur contenu au séparateur de bloc SSE. Le relais parse chaque événement JSON, agrège le texte des choix et fusionne le dernier objet `usage` reçu. `[DONE]` clôt le flux amont. EOF sans `[DONE]`, contenu non JSON, chunk non objet et `choices` mal formé deviennent des erreurs. La lecture est limitée à 185 secondes au total, avec timeouts HTTP de 185 secondes et connexion de 15 secondes. Une déconnexion du navigateur annule le relais; aucune charge n’est écrite avant l’achèvement du flux amont.

## 7. Émission SSE vers le navigateur

| event | payload | moment |
|---|---|---|
| `ready` | `{"status":"connected"}` | Après réception d’une réponse HTTP upstream non-erronée, avant le premier chunk. Le front l’ignore sans interrompre la lecture. |
| `openwebui` | `{"type":"chat:completion","data":<chunk OpenAI>}` | Pour chaque événement SSE JSON amont. |
| `settled` | `{"content":...,"charged_micro_usd":...,"balance_micro_usd":...}` | Après `[DONE]`, validation de la réponse et règlement/crédit gratuit. |
| `done` | `{"ok":true}` | Après `settled`. |
| `error` | `{"detail":"..."}` | Erreur amont, timeout, réponse incomplète, SSE invalide ou échec de débit. |

**OBSERVÉ — compatibilité du renderer** : `renderOpenWebUIEvent()` lit bien cette enveloppe (`static/app.js`, lignes 336–360). Le chemin `ready` est ignoré à `static/app.js`, lignes 96–104; le chemin `settled` est nécessaire pour que le front valide la livraison avant `done`.

## 8. Tests à exécuter manuellement après déploiement

Aucun test ni endpoint n’a été exécuté pendant cette mission. Après redémarrage par le propriétaire, remplacer les placeholders, garder le cookie dans une variable locale et utiliser `curl -N` pour conserver le flux :

```sh
curl -iN 'https://<hôte-Coach>/api/chat' \
  -H 'Content-Type: application/json' \
  -b "$COACH_COOKIE" \
  --data-binary '{"model":"<model_id autorisé>","discussion_id":"temporary:<UUID valide>","messages":[{"role":"user","content":"Réponds avec un mot."}]}'
```

Résultat attendu : HTTP 200 et événements SSE `ready`, un ou plusieurs `openwebui` avec delta(s), `settled`, puis `done`. Le delta final doit apparaître dans `settled.content`; pour un modèle payant, le solde et `credit_ledger` doivent refléter une seule charge.

```sh
curl -iN 'https://<hôte-Coach>/api/chat' \
  -H 'Content-Type: application/json' \
  -b "$COACH_COOKIE" \
  --data-binary '{"model":"<model_id autorisé>","discussion_id":"bad-id","messages":[{"role":"user","content":"test"}]}'
```

Résultat attendu : HTTP 422 avant ouverture SSE. Pour le contrôle inter-utilisateur, créer/obtenir une discussion avec le compte B, puis soumettre cet identifiant avec le cookie du compte A; résultat attendu : HTTP 404 et aucune sélection/contextualisation accessible. Vérifier enfin dans les journaux que le POST valide aboutit à `status=delivered` ou à un statut d’erreur explicite plutôt qu’à une attente silencieuse.

## 9. Points de fragilité / à confirmer

- **À confirmer** : Open WebUI accepte `tool_ids` avec `stream: true`; ce cas n’était pas validé dans le diagnostic précédent. Si le flux échoue avec les outils activés, comparer au test manuel sans `tool_ids`.
- **À confirmer** : Open WebUI accepte `max_tokens` avec `stream: true` dans cette installation et ce proxy. Il est conservé comme demandé, mais son interaction n’a pas été testée ici.
- **À confirmer** : l’ancien `params.function_calling: 'native'` n’est plus transmis, car le nouveau corps demandé est minimal et cette option n’a pas été validée avec le SSE HTTP direct. Vérifier le comportement des appels d’outils en streaming.
- **À confirmer** : les chunks de cette instance contiennent `usage.cost` ou les champs de tokens attendus dans le dernier événement; le code conserve les deux stratégies existantes, coût provider s’il existe, sinon estimation par tokens, avec débit maximal en secours.
- **NON OBSERVÉ — exécution réelle** : ni le service, ni l’endpoint, ni Open WebUI, ni la base n’ont été sollicités. Le contenu et la disponibilité effective du bridge restent à vérifier après redémarrage.
- **NON OBSERVÉ — tests automatisés** : aucun test n’a été lancé, conformément à la demande de ne pas exécuter l’application/endpoints et sans demande de tests.
