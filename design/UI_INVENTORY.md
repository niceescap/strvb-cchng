# Coach UI Inventory — État de référence (2026-10-19)

**Objectif** : fournir à Grok 4.7 un inventaire complet, précis et figé des fondations UI actuelles.
**Règle absolue** : cet inventaire décrit ce qui existe. Toute refonte de style doit préserver 100 % des comportements fonctionnels, identifiants DOM critiques, contrats d’API, et sélecteurs JS.

## 1. Architecture des pages

- Page publique :
  - `/login` → `templates/login.html` (login-card, formulaire email+password)
  - `/signup` (si ALLOW_SIGNUP=1) → `templates/signup.html`
- Page principale (après auth) :
  - `GET /app` → `templates/coach.html` (shell + chat + panneau latéral)
- Assets :
  - `/static/style.css`
  - `/static/app.js` (SPA-like, tout le rendu live, SSE, interactions)

Aucune autre route HTML. Pas de pages dédiées par fonctionnalité.

## 2. Structure DOM principale (coach.html) — IDs et classes critiques

**Shell & navigation**
- `.shell` (flex column, height 100dvh)
- `.topbar` (header 48px, gradient bleu, avatar)
  - `#open-settings` (bouton avatar, aria-controls, aria-expanded)
- `#overlay` (overlay pour fermer le panneau)
- `#settings-panel.settings` (aside slide-in, `.open` pour visible)
  - `#close-settings`

**Zone chat principale**
- `main.chat`
- `#messages.messages` (overflow auto, role=log)
  - `.welcome` (titre + p)
  - `.message` + `.user` / `.assistant`
    - `.bubble`
    - `.icon`
  - `.chat-status` (texte permanent sous le fil)
- `#chat-form.composer`
  - `#chat-input` (textarea auto-resize, maxlength 3000)
  - bouton submit

**Panneau paramètres (settings-body) — sections**
- Carte Profil athlète
  - `dl.profile`
  - `form#athlete-profile-form.profile-editor`
    - `#profile-weight`, `#profile-ftp`, `#profile-hrmax`
    - `#profile-status`
- Carte Compte Strava (`.strava-card`)
  - `#sync-strava`, `#sync-status`
  - `.strava-advanced` (details)
- `.pair` (deux cartes côte à côte)
  - Crédit : `#credit-meter.meter`, `#credit-label`, bouton → `#credit-dialog`
  - Modèle : `#model-choice` (select peuplé par JS)
- Carte Niveau : `#level-card` + `#level-snapshot`
- Carte Timeline :
  - Contrôles : `#filter`, `#sort`
  - `.table-scroll` > `table` > `tbody#timeline`
  - `#context-status.context-status`
- Formulaire logout

**Dialogs**
- `dialog#detail` : `#detail-title`, `#detail-body`
- `dialog#credit-dialog` : formulaire coupon `#coupon-form`, `#coupon-status`

**Éléments live créés dynamiquement par app.js**
- `.live-reasoning` (details > summary + .live-reasoning-text)
- `.live-tools` (ul > li avec checkbox)
- `.live-artifacts` + `.live-artifact`
- `.answer-actions` + bouton "Mémoriser la réponse"
- `.model-label` (dans bubble assistant)
- Lignes `.hint` pour coût/solde

## 3. États et interactions (JS-driven)

- Ouverture/fermeture panneau : classes `open` + `inert` + overlay
- Sélection contexte : `.context-toggle`, `.selected`, Set `selectedItems`
- Chat streaming : `busy`, textarea resize, pending bubble + live views
- SSE events traités : `openwebui`, `settled`, `done`, `error`
- Rendu live : raisonnement repliable, outils avec checkbox, artefacts (text/embed)
- Mémorisation : POST `/api/artifacts/response` seulement après `settled`
- Timeline : filter + sort client-side, clic → `detail()`, toggle contexte séparé
- Crédit : mise à jour live du meter + label après redeem ou settled
- Langue : `lang` fr/en, `copy` dict, impact sur rendu dates/nombres

**Contrats à ne jamais rompre**
- Tous les `id` et classes utilisés par les querySelector/getElementById dans app.js
- Structure des events SSE consommés par `renderOpenWebUIEvent`
- Format des items timeline retournés par `/api/timeline`
- Ordre et présence des colonnes du tableau (Date, Type, Titre, Durée, Distance, Contexte)
- Boutons "Voir le JSON compact" et "Résumé course · segment continu le plus long"

## 4. Composants visuels actuels (style.css)

Tokens racines actuels :
```css
--blue: #4361ee
--border: #dbe2ee
--ink: #202638
--muted: #68748a
```

Primitives :
- `.card` (fond blanc, border, radius 10px, padding 16px)
- `.bubble` (assistant: #eaf3ff ; user: #e8f5e9)
- `.topbar` gradient 110deg #4361ee → #3f37c9
- `.meter` (barre de progression verte)
- `table` sticky thead, hover rows
- `.context-toggle` (border bleu, .selected vert)
- `dialog` natif + ::backdrop
- `.settings` transform translateX + transition
- Responsive : `@media(max-width:600px)` simplifie grilles et paddings

Aucune ombre lourde, aucun glassmorphism, aucune typographie custom, pas de dark mode, pas d’icônes système sophistiquées.

## 5. Flux utilisateur complets (à préserver)

1. Auth : login → /app (ou signup si activé)
2. Premier affichage : welcome + chargement models + timeline + level + contexte
3. Chat : saisie → envoi → streaming live (raisonnement + outils + artefacts) → settled (coût + bouton mémoriser) → conversation en mémoire
4. Contexte : toggle item → POST /items → re-render + status
5. Détail activité/artefact : clic ligne → dialog + boutons compact
6. Strava : connect (via /auth) → query param → sync initial ou refresh
7. Crédit : dialog coupon → redeem → mise à jour solde live
8. Profil : formulaire → POST /api/profile → rechargement level
9. Mémoriser réponse → POST /api/artifacts/response → rechargement timeline

## 6. Contraintes de non-régression structurelles

- Les IDs suivants doivent rester stables (sélection JS) :
  open-settings, settings-panel, overlay, messages, chat-form, chat-input, timeline, filter, sort, context-status, model-choice, credit-meter, credit-label, level-snapshot, detail, detail-title, detail-body, sync-strava, sync-status, athlete-profile-form, profile-status, coupon-form, coupon-status, language, profile-weight/ftp/hrmax, add-credit, credit-dialog
- Classes critiques pour rendu live et styles :
  message, user, bubble, live-reasoning, live-tools, live-artifacts, live-artifact, answer-actions, context-toggle, selected, meter, card, composer, settings, strava-card, etc.
- Le contrat SSE (enveloppe openwebui + settled + done) reste identique.
- Le panneau reste le seul moyen d’accéder aux contrôles (pas de modale globale).
- La conversation reste volatile (pas de persistance côté client).
- Aucun nouveau endpoint ni nouveau paramètre de requête ne doit être inventé dans le cadre d’une refonte de style.

## 7. Contenu et données visibles (exemples de rendu)

- Timeline : mélange activités (🔶) + artefacts (📄)
- Level snapshot : lvl/100, tendance, FTP, FTP w/kg, scores par composante
- Compact JSON : préformaté, avec compte de caractères
- Artefacts Markdown : rendu brut pre + bouton download .md
- Coût : affiché en micro-usd formaté après settled (sauf gratuit)

---

Ce document + les autres fichiers de `/design/` constituent la source de vérité pour toute refonte de style par Grok 4.7.
