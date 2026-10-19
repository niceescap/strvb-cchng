# Checklist de non-régression fonctionnelle — Coach UI Style Refit

**Règle** : Avant de valider toute proposition de style, le designer et le relecteur doivent cocher tous les points. Toute modification qui fait échouer un point est invalide.

## 1. Identifiants DOM critiques (doivent rester exactement les mêmes)

Coché seulement si le sélecteur JS ou l’attribut HTML n’a pas changé.

- [ ] `id="open-settings"`
- [ ] `id="settings-panel"`
- [ ] `id="overlay"`
- [ ] `id="close-settings"`
- [ ] `id="messages"`
- [ ] `id="chat-form"`
- [ ] `id="chat-input"`
- [ ] `id="timeline"`
- [ ] `id="filter"`
- [ ] `id="sort"`
- [ ] `id="context-status"`
- [ ] `id="model-choice"`
- [ ] `id="credit-meter"`
- [ ] `id="credit-label"`
- [ ] `id="level-snapshot"`
- [ ] `id="detail"`
- [ ] `id="detail-title"`
- [ ] `id="detail-body"`
- [ ] `id="sync-strava"`
- [ ] `id="sync-status"`
- [ ] `id="athlete-profile-form"`
- [ ] `id="profile-status"`
- [ ] `id="coupon-form"`
- [ ] `id="coupon-status"`
- [ ] `id="language"`
- [ ] `id="profile-weight"`, `id="profile-ftp"`, `id="profile-hrmax"`
- [ ] `id="add-credit"`
- [ ] `id="credit-dialog"`

## 2. Classes structurelles critiques (ne pas supprimer ni renommer sans contrepartie exacte)

- [ ] `.shell`, `.topbar`, `.chat`, `.messages`, `.composer`
- [ ] `.message`, `.user`, `.bubble`, `.icon`
- [ ] `.settings`, `.settings.open`, `.settings-head`, `.settings-body`
- [ ] `.card`, `.section-head`, `.profile`, `.profile-editor`
- [ ] `.strava-card`, `.strava-advanced`, `.strava-connect`
- [ ] `.meter`, `.scale`
- [ ] `.table-scroll`, `table`, `th`, `td`
- [ ] `.context-toggle`, `.context-toggle.selected`, `.context-status`, `.context-status.has-selection`
- [ ] `.live-reasoning`, `.live-tools`, `.live-artifacts`, `.live-artifact`, `.live-artifact-body`
- [ ] `.answer-actions`
- [ ] `.welcome`, `.chat-status`, `.hint`, `.error`, `.markdown`
- [ ] `.login-page`, `.login-card`
- [ ] `.pair`, `.overlay`, `dialog`

## 3. Contrats JavaScript (static/app.js) — comportement inchangé

- [ ] `renderOpenWebUIEvent(event, live, pending)` reçoit toujours `{type, data}` avec les mêmes sous-types (chat:completion, response:..., files, embeds, artifact, status, etc.)
- [ ] `appendReasoning`, `appendAnswer`, `liveToolStep`, `addLiveArtifact`, `addRememberButton` continuent de fonctionner
- [ ] `selectedItems` (Set) + `toggleContext` + re-render du tableau
- [ ] Gestion `busy`, textarea auto-resize, conversation en mémoire
- [ ] `updateCreditBalance(micro)`, `addCostLine`
- [ ] `load()`, `render()`, `detail()`, `showCompact()`
- [ ] Gestion langue fr/en via `copy` et `lang`
- [ ] Ouverture panneau via `#open-settings`, fermeture via overlay + Escape + bouton

## 4. Flux utilisateur complets (à tester manuellement après style)

- [ ] Connexion → page /app avec welcome
- [ ] Ouverture/fermeture du panneau latéral (desktop + mobile)
- [ ] Saisie + envoi message → apparition bulle user → streaming (raisonnement + outils + artefacts) → settled + coût + bouton mémoriser
- [ ] Mémoriser une réponse → réapparition dans timeline en tant qu’artifact
- [ ] Toggle contexte sur activité et artifact → statut mis à jour + rechargement contexte
- [ ] Clic ligne timeline → dialog avec contenu + boutons compact (activité)
- [ ] Download .md depuis un artifact
- [ ] Changement de modèle (select)
- [ ] Modification profil (poids/FTP/FCmax) → rechargement level
- [ ] Redeem coupon → solde mis à jour live
- [ ] Sync Strava (bouton) → mise à jour timeline
- [ ] Filtre + tri de la timeline
- [ ] Logout

## 5. États visuels qui doivent rester fonctionnels et visibles

- [ ] Streaming en cours (live-reasoning ouvert puis replié automatiquement)
- [ ] Artefacts en direct (embed et texte)
- [ ] Outils avec checkbox (en cours / terminé)
- [ ] Contexte sélectionné (bouton vert + statut)
- [ ] Erreur chat (bulle retirée ou message système)
- [ ] Crédit insuffisant (402)
- [ ] Modèles indisponibles
- [ ] Timeline vide
- [ ] Dialogs (détail, crédit)
- [ ] Responsive < 600px (tableau, grilles, paddings)

## 6. Accessibilité et clavier (à vérifier)

- [ ] Focus visible sur tous les contrôles interactifs
- [ ] Tab / Shift+Tab dans le panneau
- [ ] Escape ferme dialog ou panneau
- [ ] aria-* existants conservés ou améliorés
- [ ] Labels et sr-only présents
- [ ] Contraste texte / fond respecté (surtout muted et states)

## 7. Règles d’or à ne jamais violer pendant la refonte de style

1. Ne jamais modifier `app.py`, `services/`, `templates/*.html` (sauf si le propriétaire l’autorise explicitement plus tard).
2. Ne jamais changer la structure des events SSE.
3. Ne jamais ajouter de nouveaux endpoints ou paramètres pour “faire joli”.
4. Ne jamais supprimer des classes ou IDs “parce que c’est moche”.
5. Si on ajoute une nouvelle classe, elle doit être purement additive (pas de suppression de l’ancienne).
6. Les transitions et animations ne doivent jamais bloquer l’interaction ni masquer du contenu critique.
7. Le fichier `static/style.css` peut être réorganisé et enrichi en variables, mais le rendu final doit rester 100 % compatible avec le HTML et le JS existants.

## 8. Validation finale recommandée (après application du style)

1. `python -m py_compile app.py` (doit passer)
2. Ouverture en navigateur (desktop + mobile viewport)
3. Parcours complet des 10 flux listés en section 4
4. Vérification que le streaming live reste lisible et que les boutons “Mémoriser”, “Ajouter au contexte”, “Voir JSON compact” restent cliquables et fonctionnels
5. Vérification que le panneau latéral s’ouvre/ferme correctement
6. Aucun nouveau bug visuel sur les états d’erreur ou de streaming long

---

**Signature** : tout designer ou agent qui propose du CSS pour Coach doit attester avoir lu et validé cette checklist avant livraison.
