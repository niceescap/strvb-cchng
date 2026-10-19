# Rapport SE1310M — garde sur `submit_task`

## OBSERVÉ

- `relay()` initialise `submit_task = None` (`app.py:714`), puis crée la tâche HTTP pour `/api/chat/completions` avant d’entrer dans la boucle d’événements (`app.py:717–720`). Cette création est commune aux modèles gratuits et payants ; elle n’est pas conditionnée par le pré-contrôle ou la tarification.
- Si la tâche HTTP termine avec succès pendant que Coach attend un événement Socket.IO, `ensure_upstream_accepted(submit_task.result())` valide la réponse puis le code met `submit_task = None` (`app.py:729–736`). La boucle continue ensuite à attendre les événements. Si un nouvel intervalle d’attente expire avant la réception de l’événement attendu, l’ancien code appelait `submit_task.done()` sans vérifier que la variable n’était plus `None`.
- Cause exacte de l’exception rapportée : après l’acceptation de la réponse HTTP, `submit_task` est explicitement remise à `None`; le prochain timeout atteint l’accès `.done()` et déclenche `AttributeError: 'NoneType' object has no attribute 'done'`.
- Correction locale appliquée à `app.py:729` : tester `submit_task is not None` avant `submit_task.done()`. La tâche n’est vérifiée que tant qu’elle existe. Aucun changement au pré-contrôle, à la formule de débit, à `charge_error` ou au texte d’erreur utilisateur.
- Le chemin du modèle gratuit et celui du modèle payant partagent cette même boucle de streaming. La différence gratuit/payant concerne ensuite le règlement (`is_free`, après réception complète), pas la création de `submit_task`. Le fait que la course soit apparue sur les modèles payants seulement est compatible avec un décalage de timing entre la fin HTTP et l’arrivée des événements Socket.IO ; le code ne comporte pas de branche de création de tâche spécifique au modèle payant.
- Compilation réussie avec `/home/nicee/coach/.venv/bin/python -m py_compile app.py` (code retour 0).
- Aucun service n’a été lancé ou redémarré, aucun message n’a été envoyé à un modèle et aucune donnée n’a été écrite en base.

## NON OBSERVÉ

- Le comportement après correction en conditions réelles, y compris la réception complète des événements et le débit final, reste à vérifier par Nicolas.
- Aucun nouveau relevé de `journalctl` ni essai avec modèle gratuit/payant n’a été effectué.

## Fichiers modifiés

- `app.py` — garde de présence avant l’appel à `.done()`.
- `rap_se1310m.md` — présent compte-rendu.

## Après le prochain essai

Après le prochain échange, consulter le service avec :

```sh
journalctl -u coach-prototype.service --since "10 minutes ago" --no-pager -o cat
```

Vérifier que l’`AttributeError` sur `submit_task.done()` ne réapparaît pas, que le flux se termine, et que pour un modèle payant le débit/la jauge ne changent qu’après livraison complète de la réponse.
