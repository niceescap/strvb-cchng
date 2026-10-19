# Réparation du streaming /api/chat — 2026-10-18

## 1. Symptôme reproductible

Symptôme rapporté dans les logs du 2026-10-18 : sur quatre POST consécutifs, deux livraisons journalisées et affichées ont été suivies de deux flux sans ligne applicative `chat` et dont la bulle a disparu après un court affichage.

```text
15:32:00  POST /api/chat 200 OK
          chat user_id=2 model_id=coach-par-claude prompt_tokens=1121
          completion_tokens=207 charged=2156 status=delivered

15:44:49  POST /api/chat 200 OK
          chat user_id=29 model_id=coach-par-claude prompt_tokens=1896
          completion_tokens=224 charged=3016 status=delivered

15:45:12  POST /api/chat 200 OK — aucune ligne applicative chat rapportée
15:46:45  POST /api/chat 200 OK — aucune ligne applicative chat rapportée
```

Les extraits proviennent du signalement de mission; ils n’ont pas été relus directement dans `journalctl`. **À confirmer** : quel événement Open WebUI a précédé les deux flux silencieux. Les logs seuls ne contiennent ni les chunks ni les terminaisons SSE nécessaires pour désigner une cause runtime unique.

## 2. Diagnostic

### Cartographie serveur avant patch

- **OBSERVÉ — signature** : `chat(request, user=Depends(current_user), db=Depends(get_db))` était à `app.py:620`; la validation de `discussion_id`, le contexte, l’allowlist, le tarif, le solde et la construction du body upstream précédaient le `StreamingResponse` (avant patch, environ lignes 620–700). Ces refus produisent une réponse HTTP non-200, pas le pattern POST 200 décrit.
- **OBSERVÉ — iter_sse_data()** : la fonction imbriquée était à `app.py:701–732`. Elle gardait un buffer entre les fragments `aiter_bytes()`, utilisait `codecs.getincrementaldecoder('utf-8')`, accumulait les lignes `data:` multiples et traitait les lignes délimitées par LF ou CRLF. Elle finalisait le décodeur et émettait le dernier champ `data:` même si le flux finissait sans séparateur final.
- **OBSERVÉ — relay()** : elle commençait à `app.py:734`. Elle parcourait le flux sous une limite de 185 secondes, ajoutait `choices[].delta.content`, mémorisait `finish_reason` et fusionnait le dernier `usage` vu. Elle reconnaissait `[DONE]` après `strip()`, donc également `data: [DONE]\r\n`. Les délimitations TCP arbitraires et les accents/emoji coupés entre fragments étaient déjà couverts par le buffer et le décodeur incrémental.
- **OBSERVÉ — sorties silencieuses identifiées** : la branche « `[DONE]` mais contenu agrégé vide ou `finish_reason == 'length'` » envoyait `error` puis retournait sans log applicatif (avant patch, vers `app.py:777–782`). `asyncio.CancelledError` était relancée sans log (près de la fin de `relay()`, actuellement `app.py:863–868`); `GeneratorExit` n’était pas interceptée. EOF sans `[DONE]` passait déjà par un `ValueError` et était loggé comme `invalid_sse`; le patch lui donne son statut `incomplete` dédié. Ces chemins peuvent expliquer une absence de ligne `status=delivered` sans exception non gérée.
- **OBSERVÉ — erreurs déjà loggées** : timeout asyncio/HTTPX écrivait `status=timeout`; HTTP status, erreur réseau, parsing invalide et exception inattendue passaient par `_log_chat_stream_exception()` avec statut explicite (avant patch, vers `app.py:868–886`; helper `app.py:90–97`). Il n’y avait donc pas de preuve d’une exception ordinaire totalement silencieuse dans ces handlers.
- **OBSERVÉ — facturation avant patch** : `charge_response()` se trouvait dans la seule branche payante, après `[DONE]` et contrôle de contenu (vers `app.py:844–857` avant patch). La branche de contenu vide ne facturait pas, mais elle ne journalisait pas son retour. La branche de déconnexion détectée avant règlement retournait également sans charge.

### Causes candidates

| Candidate | Comportement du code avant patch | Conclusion et reproduction possible | Correction |
|---|---|---|---|
| Chunk JSON coupé par TCP | `iter_sse_data()` conservait le buffer texte jusqu’à la ligne complète (`app.py:702–725` avant patch); le front gardait aussi `buffer` entre `reader.read()` (`static/app.js:86–115`). | **Écartée pour une coupure TCP ordinaire**, au niveau du code. Une réponse fragmentée peut se reproduire avec un faux upstream qui coupe un bloc JSON au milieu; ce faux upstream n’a pas été lancé. | Aucun changement de stratégie de buffer; revue conservée et décrite. |
| Caractère UTF-8 coupé entre fragments | Décodeur incrémental côté serveur et `TextDecoder.decode(..., {stream: !done})` côté front (`app.py:704,720`; `static/app.js:86,108`). | **Écartée pour une coupure valide entre octets**. Un fragment UTF-8 réellement invalide déclenche maintenant un statut `invalid_sse` explicite. | Aucun changement de décodeur nécessaire. |
| `[DONE]` non détecté avec CRLF ou fragmenté | Le serveur terminait une ligne en retirant `\r`, puis appliquait `strip()` à `[DONE]` (`app.py:706–716,750–755` avant patch). | **Écartée pour LF/CRLF, espaces périphériques et fragments**. Les fins de ligne CR seules restent **à confirmer** et ne sont pas garanties par ce parseur orienté LF/CRLF. Avant patch, EOF sans `[DONE]` était loggé sous `invalid_sse`, pas silencieux. | EOF sans `[DONE]` produit maintenant `status=incomplete`, un event `error`, et aucune facturation (`app.py:802–806`). |
| `finish_reason: stop` avec `delta.content: ""` | Le serveur ajoutait uniquement les valeurs `delta.content` de type chaîne; la chaîne vide ne supprimait pas les deltas précédents (`app.py:770–777` avant patch). Le renderer ne finalise pas sur `finish_reason`; il attend l’event `done` (`static/app.js:103–115`). | **Écartée seule** : une chaîne vide dans `delta` ne vide pas l’agrégat. En revanche, un snapshot de premier niveau `content: ""` appelait `appendAnswer(..., true)` et remplaçait le texte affiché (`static/app.js:371` avant patch); c’est une vulnérabilité réelle d’affichage, mais **à confirmer** comme cause des deux occurrences. | `appendAnswer()` ignore maintenant les chaînes vides; `settled.content` vide ne remplace plus le texte streamé (`static/app.js:118–121,312–315`). Le serveur agrège également les snapshots non vides `content` et `output` (`app.py:778–796`). |
| Erreur dans un chunk SSE amont | Les chunks sans `choices[].delta.content` étaient ignorés comme texte, y compris un objet portant `error`; suivi de `[DONE]` et texte vide, cela menait au retour silencieux incomplet. | **Cause candidate réelle** pour la combinaison « pas de ligne + pas de `settled` ». Reproductible avec un upstream renvoyant `data: {"error":...}` puis `[DONE]`; comportement exact de cette installation **à confirmer**. | Le champ `error` truthy est traité immédiatement comme `status=upstream_error`, sans charge (`app.py:763–767`). |
| Exception non loggée | Les exceptions `httpx`, JSON/UTF-8 et ordinaires étaient déjà capturées; les sorties anticipées « incomplet » et annulation ne l’étaient pas toutes. | **Partiellement réelle** : pas de silencieux pour les exceptions usuelles déjà couvertes, mais retours et annulations silencieux confirmés. | Logs ajoutés pour incomplet, cancellation, fermeture du générateur et toutes les sorties ordinaires du relay (`app.py:801–887`). |
| `settled` concurrencé par un dernier `openwebui` | Le serveur sérialise les `yield`: chaque chunk `openwebui` est envoyé pendant la boucle; `settled` n’est construit qu’après `[DONE]` et sortie de cette boucle (`app.py:781–800` avant patch). Le lecteur du navigateur traite les blocs dans l’ordre. | **Écartée dans ce code**; aucun traitement asynchrone parallèle des événements n’existe. | Aucun changement nécessaire. |
| Déconnexion navigateur / flux interrompu | `CancelledError` était relancée sans log. Dans le front, tout échec supprimait la bulle partiellement affichée (`static/app.js:124–127` avant patch). | **Cause candidate réelle** pour disparition du texte et absence de statut final; occurrence exacte **à confirmer**. Il n’y a pas de reconnexion automatique du `fetch` SSE. | Log de cancellation/fermeture côté serveur; le front conserve le texte partiel sur erreur réseau/EOF, et n’efface que pour un event `error` explicite (`app.py:862–867`, `static/app.js:103,124–126`). |

## 3. Changements appliqués dans app.py

- **`iter_sse_data()` — lignes 701–732** : inchangée dans son principe après audit. Son buffer persistant, décodeur UTF-8 incrémental, collecte des lignes `data:` et prise en charge LF/CRLF couvrent les fragments normaux. L’EOF sans `[DONE]` est maintenant explicitement journalisé par `relay()` (`app.py:801–805`). Le parseur ne promet pas le séparateur SSE à CR seul.
- **`relay()` — lignes 734–888** : traite désormais un chunk d’erreur upstream comme échec et l’arrête avant règlement (`app.py:763–767`). L’agrégat reprend les deltas, et aussi `content`/`output` non vides afin qu’un snapshot rendu par le front ne soit pas absent du `settled.content` (`app.py:768–801`). Le timeout global de 185 secondes inclut l’ouverture HTTP et la lecture (`app.py:741–750`). EOF sans `[DONE]`, `[DONE]` sans texte, `finish_reason=length` et déconnexion avant règlement ont chacun un statut loggé et ne sont pas facturés (`app.py:802–815`). `CancelledError` et `GeneratorExit` sont loggées puis relancées (`app.py:863–868`). Timeouts, HTTP, réseau, JSON/UTF-8 et erreurs inattendues restent loggés explicitement (`app.py:869–887`). Le log `status=delivered` n’est émis qu’après les `yield settled` et `yield done` (`app.py:859–862`).
- **`chat()` — lignes 619–695** : signature, validation de `discussion_id`, ownership du bridge, message système, allowlist, calcul de `max_charge`, contrôle de solde, `charge_response`, contexte et payload HTTP SSE inchangés. Le `StreamingResponse` est à `app.py:890–893`; aucune architecture Socket.IO ni identifiant de chat Open WebUI n’a été réintroduit. L’état `stream_started` est loggé à `app.py:889`.
- **Facturation** : l’appel unique à `charge_response()` demeure dans l’unique branche payante (`app.py:846–851`), après `[DONE]`, texte non vide et `finish_reason` acceptable. Les chunks d’erreur, EOF prématuré, réponses vides, limite de tokens, timeouts et déconnexions avant débit n’atteignent pas cet appel.

## 4. Changements appliqués dans static/app.js

Modifications appliquées :

- Le lecteur possédait déjà un `TextDecoder` incrémental et un buffer persistant entre lectures (`static/app.js:86–115`); aucune réécriture du parseur SSE n’était nécessaire.
- `settled.content` vide ou blanc retombe maintenant sur le texte déjà streamé, et ne remplace jamais la bulle par une chaîne vide (`static/app.js:118–121`).
- `appendAnswer()` ignore une chaîne vide, y compris un snapshot de premier niveau `content: ""` ou un bloc texte vide (`static/app.js:312–315`; appel du snapshot à la ligne 371).
- En cas d’erreur explicite SSE, le comportement d’erreur reste visible et la bulle peut être retirée. En cas d’interruption/EOF/réseau sans event `error`, le texte déjà reçu est conservé avec le message d’état (`static/app.js:103,124–126`).

Le front ne traite pas `finish_reason` comme une fin de flux; il attend `done` (`static/app.js:103–117`). Il traite `settled` sans écrasement immédiat (`static/app.js:97–102`) et parse les events `openwebui`, `settled`, `done` et `error` dans le lecteur (`static/app.js:88–105`).

## 5. Nouveau comportement des logs

| statut | condition | niveau | message type |
|---|---|---|---|
| `stream_started` | Requête validée, réponse SSE construite; couvre aussi une déconnexion avant le premier tour du générateur | INFO | `chat user_id=… model_id=… status=stream_started charged=0` |
| `delivered` | `[DONE]`, texte complet, règlement terminé et events finaux émis | INFO | `chat user_id=… model_id=… prompt_tokens=… completion_tokens=… charged=… status=delivered` |
| `incomplete` | EOF avant `[DONE]`, texte agrégé vide ou `finish_reason=length` | INFO | `status=incomplete charged=0 reason=eof_without_done/empty_content/length_finish_reason` |
| `upstream_error` | Chunk SSE JSON avec champ `error` truthy | ERROR | `status=upstream_error charged=0 error_chunk=1` |
| `upstream_http_error` | Réponse HTTP amont non-2xx | ERROR | `status=upstream_http_error charged=0 …` avec résumé amont expurgé |
| `upstream_error` | Erreur réseau HTTPX amont | ERROR | `status=upstream_error charged=0 …` |
| `invalid_sse` | JSON, choix ou UTF-8 invalide | ERROR | `status=invalid_sse charged=0 …` |
| `timeout` | Timeout total ou HTTPX | INFO | `status=timeout charged=0` |
| `client_disconnected` | `request.is_disconnected()` avant règlement ou `GeneratorExit` | INFO | `status=client_disconnected charged=0/…` |
| `cancelled` | Annulation asyncio | INFO | `status=cancelled charged=0/…` |
| `charge_error` | Échec SQLAlchemy lors du débit/journal | ERROR | `status=charge_error … charged=unknown` (le commit peut avoir précédé une erreur de lecture du solde; rapprochement du ledger nécessaire) |
| `stream_error` | Toute autre exception du relay | ERROR | `status=stream_error charged=0 …` |

Les exceptions du tableau passent par `_log_chat_stream_exception()` (`app.py:90–97`) ou par un log dédié dans `relay()` (`app.py:801–887`). `stream_started` est aussi loggé avant le `StreamingResponse` (`app.py:889`), de sorte qu’une déconnexion avant même le premier avancement du générateur laisse une trace. Les refus avant création du `StreamingResponse` restent des réponses HTTP ordinaires (`app.py:623–682`); ils ne correspondent pas à un POST 200 sans fin de flux.

## 6. Garanties conservées

- **Facturation appelée une seule fois** : oui, un seul appel à `charge_response()` dans une seule branche payante (`app.py:844–850`).
- **Pas de facturation sur réponse incomplète** : oui; aucun appel avant `[DONE]`, texte non vide et `finish_reason` différent de `length` (`app.py:801–850`).
- **Format SSE navigateur inchangé** : oui; `ready`, enveloppe `openwebui`, `settled`, `done`, `error` sont conservés.
- **Pas de retour à Socket.IO** : confirmé par inspection du source; aucun import/usage `socketio`, `sio`, `user-join` ni `events:chat` ne subsiste dans `app.py`.
- **Pas d’identifiant de chat envoyé à Open WebUI** : body limité à `model`, `messages`, `stream`, `max_tokens` et `tool_ids` facultatif (`app.py:684–692`); pas de `chat_id`, `id`, `session_id` ou `user_message`.
- **Contexte conservé** : le payload lié à l’utilisateur reste préfixé dans le message système (`app.py:637–654`).

## 7. Tests à exécuter manuellement après restart

Aucun endpoint, application ni test automatique n’a été lancé pour cette mission. Une reproduction **fiable** ne peut pas être garantie par `curl` seul sans connaître le chunk upstream exact qui a précédé les deux échecs; cette information est **à confirmer**. Le script ci-dessous est un test séquentiel de diagnostic, pas une reproduction garantie. Il varie la taille du message et utilise des discussions sans item sélectionné.

```sh
for size in 8 512 2048 3500; do
  discussion_id="temporary:$(/home/nicee/coach/.venv/bin/python -c 'import uuid; print(uuid.uuid4())')"
  message=$(head -c "$size" /dev/zero | tr '\000' 'x')
  body=$(printf '{"model":"<model_id autorisé>","discussion_id":"%s","messages":[{"role":"user","content":"%s"}]}' "$discussion_id" "$message")
  curl -sS -N -i 'https://<hôte-Coach>/api/chat' \
    -H 'Content-Type: application/json' -b "$COACH_COOKIE" --data-binary "$body"
done
```

Pour un passage avec contexte, créer un nouvel ID et sélectionner un item appartenant au compte authentifié avant le POST :

```sh
discussion_id="temporary:$(/home/nicee/coach/.venv/bin/python -c 'import uuid; print(uuid.uuid4())')"
curl -sS -b "$COACH_COOKIE" -H 'Content-Type: application/json' \
  --data-binary '{"item_type":"activity","item_id":<ID activité du compte>,"selected":true}' \
  "https://<hôte-Coach>/api/context/$discussion_id/items"
curl -sS -N -i 'https://<hôte-Coach>/api/chat' \
  -H 'Content-Type: application/json' -b "$COACH_COOKIE" \
  --data-binary "$(printf '{\"model\":\"<model_id autorisé>\",\"discussion_id\":\"%s\",\"messages\":[{\"role\":\"user\",\"content\":\"analyse cette activité\"}]}' "$discussion_id")"
```

Attendu pour chaque réponse complète : événements `ready`, `openwebui` (un ou plusieurs), `settled`, `done`; journal `status=delivered` avec une seule charge pour un modèle payant. Pour les erreurs/incomplétudes : event `error`, aucun `settled`, aucune charge (sauf issue de commit signalée `charged=unknown` au statut `charge_error`), et une ligne `status=incomplete`, `upstream_error`, `invalid_sse`, `timeout` ou autre statut explicite. Observer en parallèle :

```sh
journalctl -u coach.service --since '5 minutes ago' --follow
```

## 8. Points de fragilité restants

- **À confirmer** : le format exact des chunks émis par la version Open WebUI déployée et si l’un des deux cas échoués était un chunk `error`, une réponse sans texte, ou une annulation navigateur. Les extraits de flux n’étaient pas fournis.
- **À confirmer** : présence systématique de `usage.cost`, `prompt_tokens` et `completion_tokens` sur le chunk final. Le code fusionne `usage`; si absent, il conserve l’estimation existante ou le débit maximal en secours (`app.py:817–844`).
- **À confirmer** : `tool_ids` avec `stream: true` et le comportement d’Open WebUI au EOF après une erreur d’outil. Le chunk JSON d’erreur est maintenant intercepté; les formats alternatifs non-JSON restent à confirmer.
- Le parseur upstream prend en charge LF et CRLF, mais pas un flux séparé uniquement par CR; ce format est rare mais pas couvert (`app.py:706–725`).
- Une annulation après que le règlement a été commité mais avant la confirmation du navigateur ne peut pas annuler le débit. Le statut contient alors le montant déjà réglé (`app.py:862–867`). Si `charge_response()` lève une erreur après un commit mais avant de rendre le nouveau solde, le statut `charge_error charged=unknown` nécessite un rapprochement dans `credit_ledger`; aucune répétition automatique du débit n’est faite.
- La reconnexion automatique du navigateur n’est pas ajoutée; le texte partiel reste affiché après interruption sans `error`, et une nouvelle requête reste une action utilisateur.
- **NON OBSERVÉ — runtime et tests** : aucun restart, appel au service, accès aux logs réels, ni test automatique n’a été effectué. Le résultat du patch en production reste à confirmer après déploiement par le propriétaire.
