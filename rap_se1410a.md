# Rapport SE1410A — proposition d’accès des modèles aux données utilisateur

## Objet

Proposer une méthode pour relier les harnais de modèles Open WebUI aux activités Strava et aux artefacts enregistrés par Coach, avec lecture et création contrôlées d’artefacts Markdown.

## État des lieux

- **OBSERVÉ — d’après les rapports SE1310A à SE1310M :** Coach récupère les modèles Open WebUI via une route backend authentifiée et possède un flux de chat agentique natif relayé par Socket.IO/SSE. Les rapports indiquent que le flux et le règlement après réponse ont reçu des corrections, mais la réception réelle des événements et le règlement en production restent à valider par le propriétaire.
- **OBSERVÉ — code lu :** `coach_activities` et `coach_artifacts` possèdent chacun un `user_id`. Les routes `/api/timeline` et `/api/timeline/{kind}/{item_id}` sont protégées par `current_user` et filtrent les éléments par cet utilisateur. La route de détail d’activité renvoie actuellement un résumé limité; une route séparée peut lire ou calculer le résumé compact. Les artefacts contiennent `title`, `category`, `markdown` et un `related_activity_id` facultatif.
- **OBSERVÉ — rapports SE1310C et SE1310D :** l’accès à PostgreSQL n’a pas pu être établi depuis l’environnement de travail dans ces missions; le schéma réellement déployé, les volumes et les données restent donc non observés. Aucune donnée utilisateur ne doit être nécessaire à la conception proposée.
- **OBSERVÉ — rapport SE1310I :** le chemin de streaming Open WebUI utilise un compte de service et un JWT Socket.IO distinct de la clé API HTTP. Le format des événements et l’identité Open WebUI effectivement associée à la session Coach n’ont pas été validés en conditions réelles.
- **NON OBSERVÉ :** aucune exécution d’outil par un modèle, aucun appel réel au service et aucune création d’artefact n’ont été vérifiés dans les rapports consultés.

## Recommandation

Faire de **Coach le seul gardien des données**. Le modèle ne reçoit ni connexion SQL, ni accès direct à PostgreSQL, ni secret Strava, ni droit général sur l’API. Il demande des opérations métier par outils étroits; Coach authentifie l’utilisateur, détermine son `user_id` depuis la session et applique cette identité à chaque lecture et écriture.

Les opérations initiales peuvent rester simples et explicites :

1. `list_activities` : liste paginée et bornée, avec période et filtres limités.
2. `get_activity` : résumé d’une activité appartenant à l’utilisateur.
3. `get_activity_analysis` : résumé compact déjà en cache ou calculé par le service Coach selon les règles existantes.
4. `list_artifacts` et `get_artifact` : métadonnées, puis contenu Markdown d’un artefact appartenant à l’utilisateur.
5. `create_artifact` : création d’un artefact Markdown avec titre, catégorie autorisée et référence d’activité facultative.
6. `update_artifact` : à ajouter seulement si l’édition d’un artefact existant est requise; l’identifiant doit être revalidé dans le périmètre utilisateur.

Chaque outil doit avoir un schéma d’entrée strict, des limites de taille et de pagination, des réponses réduites au besoin du modèle et des erreurs sans détails internes. Les identifiants fournis par le modèle sont des sélecteurs, jamais une preuve d’autorisation : toutes les requêtes de lecture, modification et suppression éventuelle doivent inclure le filtre `user_id` dérivé de l’identité authentifiée. Une référence `related_activity_id` doit être vérifiée comme appartenant au même utilisateur. La création et la modification doivent être transactionnelles; les appels d’écriture devraient porter une clé d’idempotence pour éviter les doublons lors d’une reprise de flux.

## Où exécuter les outils

Le point délicat est l’identité. Le rapport SE1310I décrit un compte Open WebUI de service; cette identité partagée ne suffit pas, à elle seule, à autoriser l’accès aux données de l’utilisateur Coach qui a ouvert la conversation.

Je recommande un **routeur d’outils côté Coach**, attaché à la requête de chat authentifiée. Il fournit au harnais uniquement les définitions des outils et leurs paramètres; l’exécution effective passe par du code Coach qui détient le contexte `current_user`. Le contexte serveur associe chaque conversation à un utilisateur et à un ensemble de capacités précises. Il ne faut jamais accepter un `user_id` généré par le modèle ou envoyé dans les arguments d’un outil.

Si Open WebUI doit exécuter lui-même les outils natifs, l’intégration doit transmettre à son exécuteur un contexte d’autorisation court, signé, limité à une conversation et à une liste d’opérations, puis le présenter au service Coach hors des arguments visibles du modèle. Cette liaison n’est acceptable qu’après avoir vérifié que la version déployée transporte et protège effectivement ce contexte jusqu’à l’exécution du tool. Une clé de service statique seule donnerait à l’outil une identité trop large; il ne faut pas la transformer en accès global aux données.

## Contrat d’autorisation et de sécurité

- L’identité provient de la session Coach au démarrage du chat et reste attachée côté serveur à la conversation.
- Le modèle ne choisit jamais le propriétaire des données. Les outils n’acceptent pas `user_id` en entrée.
- Le service réduit les champs retournés : résumé d’activité et analyse utile, sans jetons Strava, informations d’authentification ou champs internes sans rapport.
- L’accès aux activités Strava s’effectue à travers les services d’ingestion et d’analyse Coach; aucun jeton Strava n’est exposé au modèle ni à Open WebUI.
- L’écriture d’un artefact est attribuée au `user_id` de la conversation, avec catégorie contrôlée et vérification de la référence d’activité. Le Markdown est traité comme contenu non fiable lors de son affichage.
- Les lectures et écritures d’outils sont journalisées avec utilisateur, opération, résultat, identifiant de conversation et identifiant d’objet; les contenus sensibles complets ne sont pas recopiés dans les journaux.
- Les outils n’effectuent ni requête SQL libre ni action générique de type « exécuter du code ».

## Séquence de réalisation conseillée

1. Écrire le contrat des outils et les règles d’autorisation, sans modifier les tables.
2. Implémenter les fonctions métier Coach et leurs schémas d’entrée/sortie, réutilisant les requêtes existantes et le filtre utilisateur.
3. Attacher ces fonctions au cycle agentique, en conservant l’identité serveur à travers chaque tour d’outil. Vérifier d’abord que l’exécution des tools Open WebUI peut recevoir ce contexte sans l’exposer au modèle; sinon garder le routeur d’exécution côté Coach.
4. Commencer par les lectures; vérifier l’isolation entre deux comptes avec des identifiants d’objets croisés.
5. Ajouter `create_artifact`, puis l’édition uniquement si nécessaire. Vérifier validation, idempotence, attribution correcte et persistance.
6. Enfin vérifier que les événements du tool sont relayés en direct et que le règlement du tour reste conforme aux règles actuelles. Les opérations de données doivent réussir ou échouer indépendamment du paiement de l’inférence; le coût d’inférence ne doit pas servir de mécanisme d’autorisation des outils.

## Conclusion

Le modèle doit disposer de capacités métier très limitées, tandis que Coach conserve l’identité, l’autorisation et l’accès aux données. Cette séparation permet au modèle d’analyser les activités et de produire des artefacts utiles sans lui donner un accès général à la base ou aux comptes Strava. Le prochain point de conception à trancher techniquement est la propagation fiable de l’identité Coach dans le chemin réel d’exécution des tools Open WebUI; elle n’est pas encore observée dans les rapports.
