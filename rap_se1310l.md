# Rapport SE1310L — localisation de l’AttributeError du chat

## OBSERVÉ

- Dans `app.py`, l’exception du flux est capturée dans le `except` général de `relay()` (ligne 872). Ce chemin englobe le traitement des événements et le règlement d’un tour payé. `upstream_error` (ligne 732) est plus restreint : il capture le résultat de la requête HTTP quand celle-ci est terminée sans événement Socket.IO reçu pendant l’intervalle d’attente.
- Les deux branches appellent maintenant `logger.exception` via `_log_chat_stream_exception` (lignes 88–96). La trace conserve les frames et le type d’exception ; le texte de l’exception est remplacé par une copie expurgée des motifs courants de jetons, clés et secrets. Le statut HTTP et un extrait expurgé du corps restent journalisés lorsqu’une réponse est attachée à l’exception. Aucun en-tête d’autorisation n’est écrit.
- La requête tarifaire est à `app.py:619–622`. Elle sélectionne seulement `provider_micro_usd_per_mtok_in` et `provider_micro_usd_per_mtok_out` et filtre `active = true`. Le schéma de `model_pricing` comporte aussi `sale_multiplier` et `effective_from` (`migrations/0003_credits.sql:25–32`), mais le chemin chat ne les sélectionne ni ne les consulte et ne filtre pas sur `effective_from`.
- Pour un modèle payé, le coût maximal est calculé à `app.py:625–628`, avec `max_tokens = 2048`, le nombre de caractères en entrée et les tarifs fournisseur ; le contrôle du solde est à `app.py:632–636`. Les tarifs sont lus par index de mapping (`price['…']`), pas par accès d’attribut. Un résultat nul pour un modèle payé est rejeté avant le flux (`app.py:623–624`).
- Le corps envoyé à Open WebUI est construit à `app.py:667–689` : `stream`, `chat_id`, `id` du message assistant, `session_id`, messages, mode `native` et `max_tokens`. `tool_ids` est ajouté conditionnellement à `app.py:690–692`.
- Les champs de `usage` sont lus avec `.get()` après que `aggregate['usage']` a été créé comme dictionnaire et rempli seulement depuis des objets confirmés comme dictionnaires (`app.py:797–798`, `815–820`). Les conversions d’usage fournisseur sont entourées d’un `try/except` (`app.py:830–836`). Si les tokens manquent, l’estimation consulte les deux clés du mapping tarifaire (`app.py:837–846`).
- Le règlement réservé aux modèles payants commence à `app.py:829` et appelle `charge_response` à `app.py:847–856`. C’est la zone différentielle la plus plausible pour une erreur absente de `coach-gratuit-2` : le modèle gratuit suit la branche `is_free` (`app.py:822–828`) et ne passe ni par le débit ni par le contrôle préalable (`app.py:635–636`). Selon l’indication fournie, le modèle gratuit n’a pas de tarif actif ; le code autorise ce cas pour un modèle gratuit et calcule `max_charge = 0` (`app.py:623–628`).
- Aucun accès d’attribut évident sur `price` ou `usage` susceptible de produire à lui seul l’`AttributeError` n’apparaît dans la lecture statique : `price` est indexé comme mapping, et `usage` est un dict contrôlé. La cause exacte n’est donc pas établie sans la trace du prochain essai. Une erreur dans le chemin de règlement payé (notamment pendant l’appel SQLAlchemy à `charge_response`, lignes 847–856) est une hypothèse cohérente avec la différence gratuit/payant et `charged=0`, mais reste à confirmer par le traceback.
- Vérification demandée réussie : `/home/nicee/coach/.venv/bin/python -m py_compile app.py` (code retour 0). Aucun test, service, appel modèle ou écriture en base n’a été effectué.

## NON OBSERVÉ

- L’emplacement exact de l’`AttributeError` : aucun nouvel essai de modèle n’a été fait et aucune trace complète du prochain échec n’est disponible ici.
- Le type concret retourné par la requête SQLAlchemy en production, le contenu/la forme réelle de `usage` pour ces modèles et la présence d’un tarif actif ou sa date d’effet en base n’ont pas été vérifiés. Aucune donnée de base n’a été lue pendant cette mission.
- Le fait que le débit ne s’exécute pas comme résultat de cette exception vient du constat communiqué ; aucun essai n’a été reproduit.

## Fichiers modifiés

- `app.py` — trace complète expurgée dans `upstream_error` et `stream_error`.
- `rap_se1310l.md` — présent compte-rendu.

## Après le prochain essai

Lancer cette commande après l’essai de Nicolas pour récupérer la trace et son emplacement :

```sh
journalctl -u coach-prototype.service --since "10 minutes ago" --no-pager -o cat
```

Filtrer les lignes `status=stream_error` ou `status=upstream_error`, puis lire les frames jusqu’au type et au message d’exception expurgé. La trace déterminera si l’hypothèse du règlement payé est correcte ; aucune correction fonctionnelle n’a été appliquée.
