# Tokens et primitives CSS actuelles — Coach (référence figée)

**Source** : `static/style.css` (lecture complète 2026-10-19)
**But** : permettre à un designer LLM de comprendre exactement ce qui existe avant de proposer des évolutions.

## 1. Variables :root actuelles

```css
--blue: #4361ee;
--border: #dbe2ee;
--ink: #202638;
--muted: #68748a;
```

Aucune autre variable CSS. Tout le reste est en dur ou dérivé.

## 2. Reset & base

- `* { box-sizing: border-box }`
- `html, body { height: 100%; margin: 0 }`
- `body { background: #f5f7fb; color: var(--ink); font: 15px/1.5 system-ui, -apple-system, 'Segoe UI', sans-serif; }`
- `button, input, select, textarea { font: inherit; }`
- `button { cursor: pointer; }`
- `.sr-only` (accessibilité)

## 3. Layout principal

- `.shell` : flex column, height 100dvh
- `.topbar` : height 48px, flex none, gradient(110deg, #4361ee, #3f37c9), color white, padding 0 14px
- `.chat` : min-height 0, flex 1, width min(100%,860px), margin auto, background white, box-shadow 0 2px 12px #15204015
- `.messages` : flex 1, overflow auto, padding 22px
- `.welcome` : text-align center, max-width 550px, margin 11vh auto 0
- `.composer` : flex, gap 8px, border-top, padding
- `.composer textarea` : flex 1, min-height 42px, max-height 130px, resize none, border 1px solid var(--border), border-radius 18px

## 4. Messages et bulles

- `.message` : flex, gap 10px, margin 16px 0
- `.message.user` : flex-direction row-reverse
- `.bubble` : max-width 80%, padding 11px 14px, background #eaf3ff, border-radius 12px, white-space pre-wrap
- `.user .bubble` : background #e8f5e9
- `.message .icon`

## 5. Panneau latéral (settings)

- `.settings` : position fixed, inset 0 0 0 auto, z 6, width min(100%,760px), flex column, background #f5f7fb, box-shadow -5px 0 25px #0003, transform translateX(100%), visibility hidden, transition
- `.settings.open` : visibility visible, transform none
- `.settings-head` : min-height 53px, flex, color white, background var(--blue), padding 8px 17px
- `.settings-body` : flex 1, overflow auto, padding 14px
- `.card` : background white, border 1px solid var(--border), border-radius 10px, padding 16px, margin-bottom 14px
- `.card h3` : font-size 16px, margin 0 0 12px
- `.section-head` : flex, align center, gap 8px

## 6. Profil & formulaires

- `.profile` : display grid, 1fr 1fr, gap 8px 18px
- `.profile dt` : font-size 12px, color var(--muted)
- `.profile dd` : margin 0, font-weight 600
- `.profile-editor` : grid 1fr minmax(130px,1fr), gap 8px 12px
- input, select : padding 7px, border 1px solid var(--border), border-radius 6px, background white

## 7. Tableau timeline

- `.table-scroll` : overflow auto, max-height min(50vh,450px)
- `table` : width 100%, min-width 620px (760px dans une règle plus tard), border-collapse collapse, font-size 13px
- `th, td` : text-align left, border-bottom 1px solid var(--border), padding 8px
- `th` : position sticky, top 0, background #eef2fb
- `tbody tr` : cursor pointer, hover #eef2ff
- `td:nth-child(3)` : ellipsis

## 8. Contexte et toggles

- `.context-toggle` : white-space nowrap, border 1px solid #7b8ce8, border-radius 7px, background #fff, color #3048be, padding 6px 9px, font-size 12px, font-weight 700
- `.context-toggle.selected` : background #e7f7ee, border-color #42a477, color #146b4d
- `.context-status` : margin 10px 0 0, padding 9px 11px, border-radius 7px, background #f0f2f7, color var(--muted), font-size 13px
- `.context-status.has-selection` : background #e7f7ee, color #146b4d, font-weight 700

## 9. Live streaming (créé par JS)

- `.live-reasoning`, `.live-tools`, `.live-artifacts` : margin 10px 0, padding 8px 10px, border 1px solid var(--border), border-radius 8px, background #f8f9fc, font-size 13px
- `.live-reasoning summary`, `.live-artifact summary` : cursor pointer, color var(--muted), font-weight 600
- `.live-reasoning-text` : padding 7px 2px, white-space pre-wrap
- `.live-tools ul` : list-style none, margin 7px 0 0, padding 0
- `.live-tools li` : flex, gap 7px
- `.live-artifact` : margin-top 7px, padding 6px, border-top 1px solid var(--border)
- `.live-artifact-body pre` : max-height 400px, overflow auto
- `.answer-actions` : flex, gap 9px, margin 12px 0 0, padding-top 9px, border-top 1px solid var(--border), font-size 12px, color var(--muted)
- `.answer-actions button` : border 1px solid #7b8ce8, border-radius 7px, background #fff, color #3048be, padding 6px 10px, font-weight 650

## 10. Strava, crédit, meter

- `.strava-connect`, `.strava-card button` : background #fc4c02, color white, border-radius 7px, padding 9px 13px, font-weight 600
- `.meter` : height 18px, border 1px solid var(--border), border-radius 9px, overflow hidden, background repeating-linear-gradient(...)
- `.meter span` : height 100%, background #4caf50
- `.scale` : flex justify-between, color var(--muted)

## 11. Dialogs

- `dialog` : width min(92vw,620px), max-height 85vh, border 1px solid var(--border), border-radius 10px, padding 18px, box-shadow 0 20px 60px #0003
- `dialog::backdrop` : background #0008
- `.dialog-head` : flex, justify space-between

## 12. Login / signup

- `.login-page` : min-height 100%, display grid, place-items center, padding 15px
- `.login-card` : width min(100%,390px), padding 28px, border 1px solid var(--border), background white, border-radius 14px, box-shadow 0 7px 30px #0001

## 13. Responsive

```css
@media (max-width:600px) {
  .messages { padding:13px }
  .welcome { margin-top:7vh }
  .settings-body { padding:9px }
  .pair, .profile { grid-template-columns:1fr }
  .card { padding:12px }
  .table-scroll { max-height:50vh }
  .profile-editor { grid-template-columns:1fr }
}
@media (prefers-reduced-motion:reduce) {
  .settings { transition:none }
}
```

## 14. Divers

- `.hint` : font-size 12px, margin 8px 0 0, color var(--muted)
- `.error` : color #a22
- `.logout` : border 1px solid #a33, color #a33, background white, border-radius 6px
- `.markdown` : white-space pre-wrap, font 14px/1.7 ui-monospace, monospace, background #f5f7fb, padding 12px, border-radius 7px

## 15. Remarques importantes pour le redesign

- Beaucoup de valeurs en dur (#eaf3ff, #e8f5e9, #f5f7fb, #eef2fb, #fc4c02, #4caf50, #7b8ce8, #3048be, #42a477, #146b4d, etc.)
- Le bleu principal est très présent (#4361ee)
- Le vert Strava est codé en dur
- Les couleurs de sélection contexte et des toggles sont spécifiques
- Le fond global est gris très clair (#f5f7fb)
- Les bulles chat utilisent des bleus et verts très doux

Le designer doit décider s’il :
- Garde les mêmes valeurs sémantiques (bleu = action principale, vert = Strava/positif)
- Introduit une nouvelle palette tout en conservant les rôles
- Extrait TOUT en variables CSS modernes

**Recommandation forte** : extraire un système de design complet en variables dès le début de la refonte, même si l’implémentation reste dans un seul fichier.
