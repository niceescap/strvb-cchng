# Rapport SE1310K — diagnostic du streaming Open WebUI

## OBSERVÉ

- `app.py` avait un logger nommé, mais aucune configuration de handler ou de niveau INFO propre à Coach. Les erreurs `upstream_error` et `stream_error` ne journalisaient que la classe d’exception.
- Le client utilise `POST /api/chat/completions` et envoie `stream: true`, `chat_id`, `id` (UUID du message assistant), `session_id` (SID Socket.IO), ainsi que `user_message` et `messages`.
- L’API attend l’identifiant de message assistant dans le champ `id` : la documentation Open WebUI de l’API emploie cette forme. `message_id` est le champ d’événement Socket.IO lu par Coach pour filtrer les événements. Il n’y a donc pas d’écart de nom dans le corps HTTP. [Documentation API Open WebUI](https://docs.openwebui.com/reference/api-flow/)
- `tool_ids` est ajouté au corps uniquement si la variable `OPENWEBUI_TOOL_IDS` contient des éléments après découpage par virgule. La présence de cette variable dans l’environnement effectif du service n’a pas été vérifiée.
- `app.py` configure désormais un handler console INFO dédié pour le logger Coach. Les deux branches de diagnostic ajoutent le type d’exception et le code HTTP/corps de réponse lorsque l’exception porte une réponse. Le corps est limité à 200 caractères et les formes courantes de clés, jetons Bearer, JWT et secrets sont masquées ; aucun en-tête n’est journalisé. Le cas où Open WebUI répond avec `{ "status": false }` conserve aussi sa réponse attachée à l’exception pour le diagnostic.
- Le message SSE d’erreur envoyé à l’utilisateur est inchangé. La logique de débit, le pré-contrôle et `charge_error` n’ont pas été modifiés.
- Compilation réussie avec `/home/nicee/coach/.venv/bin/python -m py_compile app.py` (code retour 0).
- Aucun service n’a été lancé ou redémarré, aucun modèle appelé et aucune donnée écrite en base.

## NON OBSERVÉ

- Aucune nouvelle tentative de chat : la classe réelle d’exception, le statut et le corps renvoyés par Open WebUI restent inconnus.
- L’apparition effective des lignes INFO dans `journalctl` après redémarrage du service n’a pas été vérifiée. Le handler est configuré dans le processus Coach, mais le processus actuellement lancé n’a pas été relancé.
- La configuration effective de `OPENWEBUI_TOOL_IDS` dans l’environnement du service n’a pas été inspectée ; le code transmet bien ce champ lorsqu’il est renseigné.

## Fichiers modifiés

- `app.py` — handler INFO et détails d’erreur HTTP expurgés.
- `rap_se1310k.md` — présent compte-rendu.

## À vérifier après le prochain essai

Après le prochain essai de chat, consulter le journal du service avec :

```sh
journalctl -u coach-prototype.service --since "10 minutes ago" --no-pager -o cat
```

Repérer `status=upstream_error` ou `status=stream_error`, puis relever `exception_class`, `http_status` et `http_body`. Vérifier qu’aucune clé ou aucun jeton n’apparaît dans la ligne. Si aucune ligne INFO n’apparaît, le processus actif doit d’abord être redémarré par son propriétaire pour charger le changement.
