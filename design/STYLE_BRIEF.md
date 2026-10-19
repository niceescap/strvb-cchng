# BRIEF DE REFONTE DE STYLE — Coach (Premium, Didactique, Multi-proposition)

**Date** : 2026-10-19
**Cible** : Grok 4.7 (ou équivalent)
**Périmètre strict** : UNIQUEMENT le style, la présentation, la typographie, les couleurs, les espacements, les états visuels, les micro-interactions, l’ergonomie visuelle et la didactique de l’interface. **ZÉRO modification fonctionnelle.**

## 1. Principes directeurs (obligatoires)

1. **Didactique avant tout**  
   Chaque écran, chaque section, chaque contrôle doit aider l’athlète à comprendre :
   - Où il en est (niveau, contexte, crédit, modèle)
   - Ce qu’il peut faire (actions claires, affordances)
   - Pourquoi une action existe (labels, hints, progression)
   - Ce qui se passe en temps réel (streaming, sélection, coût)

2. **Hiérarchie visuelle claire et progressive**  
   - Information primaire (messages du coach, actions immédiates)
   - Information secondaire (métadonnées, timeline, niveau)
   - Information tertiaire (paramètres avancés, détails techniques)

3. **Multi-proposition**  
   Le designer doit proposer **au moins 3 directions visuelles** distinctes, chacune avec :
   - Une philosophie claire (ex. : “Minimal calme”, “Athlétique technique”, “Sérénité académique”)
   - Un jeu de tokens (couleurs, typographie, rayon, ombres, densité)
   - Des exemples de rendu (chat, carte, tableau, live streaming)
   - Les forces et les points d’attention pour l’athlète

4. **Non-régression fonctionnelle absolue**  
   - Tous les IDs DOM listés dans `UI_INVENTORY.md` restent inchangés.
   - Tous les contrats JS (renderOpenWebUIEvent, selectedItems, etc.) restent valides.
   - Tous les flux (chat SSE, toggle contexte, mémoriser, détail, Strava, coupon) restent identiques.
   - Le panneau latéral reste le seul endroit des contrôles.
   - La conversation reste volatile (pas de persistance UI nouvelle).

5. **Cohérence et sobriété premium**  
   - Jamais de surcharge. L’interface doit respirer.
   - Les états (loading, success, error, selected, disabled) sont toujours visibles et calmes.
   - Les micro-animations sont subtiles et respectent `prefers-reduced-motion`.

## 2. Public cible et contexte d’usage

- Cyclistes entraînés (route, gravel, course) qui utilisent déjà Strava.
- Utilisent Coach pour analyser leurs données, poser des questions pointues, mémoriser des réponses.
- Peuvent passer 10 à 40 minutes dans l’interface par session.
- Valeurs : précision, sérieux, pédagogie, gain de temps, confiance.

## 3. Zones critiques à traiter (priorité de refonte)

A. **Chat principal** (le cœur de l’expérience)
   - Bulle utilisateur / assistant
   - Indicateurs live (réflexion, outils, artefacts)
   - Zone de saisie + envoi
   - Message de statut conversation volatile
   - Affichage du coût et du bouton “Mémoriser”

B. **Topbar + Avatar + Panneau latéral**
   - Ouverture/fermeture fluide et accessible
   - Organisation des sections (profil, Strava, crédit, modèles, niveau, timeline)

C. **Timeline + Contexte**
   - Tableau d’activités et artefacts
   - Boutons de sélection de contexte (visuellement très clairs)
   - Statut de contexte actif
   - Détail (dialog)

D. **Crédit, Niveau, Modèles**
   - Compteur de crédit (meter + valeur)
   - Snapshot niveau (scores)
   - Sélecteur de modèle

E. **États live pendant le streaming**
   - Réflexion repliable
   - Outils (checkbox)
   - Artefacts en direct
   - Remplacement final propre

F. **Auth (login/signup)** — style cohérent avec l’app mais plus simple

## 4. Contraintes techniques et d’implémentation

- Un seul fichier CSS existant : `static/style.css` (remplacer ou enrichir les variables + règles)
- Pas de nouveau framework, pas de dépendance CSS supplémentaire
- Respect strict du HTML existant (Jinja + classes/IDs actuels)
- Responsive mobile-first déjà présent ; l’améliorer sans le casser
- Accessibilité : conserver et renforcer les aria-*, labels, focus visibles, clavier
- Performance : les ajouts de style ne doivent pas alourdir le rendu initial

## 5. Vocabulaire visuel autorisé

- Typographie système de qualité (system-ui + fallbacks propres)
- Palette limitée, haut contraste pour le texte, doux pour les fonds et accents
- Rayons modérés et cohérents
- Ombres subtiles (pas de néon ni de flat total)
- Icônes : emoji actuels ou remplacement par un set très léger (à proposer)
- États : hover, focus-visible, active, disabled, selected, loading

## 6. Livrables attendus de la refonte (pour chaque proposition)

1. **Palette complète** (primary, accent, neutres, semantic : success/warn/error, surfaces)
2. **Échelle typographique** + line-heights + font-weights
3. **Échelle d’espacement** (4/8/12/16/24/32/48 px ou tokens)
4. **Tokens de rayon, ombre, focus ring**
5. **Règles pour chaque composant majeur** :
   - Topbar
   - Chat (messages, bubbles, composer, live zones)
   - Carte (card)
   - Tableau timeline
   - Boutons context-toggle et actions
   - Panneau latéral + overlay
   - Dialogs
   - Meters, selects, inputs, forms
6. **Exemples de rendu** (description textuelle ou pseudo-code CSS pour) :
   - État vide / welcome
   - Message utilisateur + assistant avec réflexion ouverte puis fermée
   - Streaming en cours (outils + artefacts)
   - Réponse mémorisée + coût affiché
   - Timeline avec 2 activités + 1 artefact sélectionnés
   - Panneau ouvert sur mobile
7. **Règles didactiques spécifiques** (exemples) :
   - Comment rendre le statut de contexte plus compréhensible
   - Comment indiquer “cette réponse est temporaire sauf si mémorisée”
   - Comment présenter le coût sans anxiété
   - Comment guider le premier usage du sélecteur de contexte

## 7. Anti-modèles (à éviter absolument)

- Ajout de nouveaux endpoints ou de nouveaux paramètres d’URL
- Changement de structure HTML qui casserait les querySelector de app.js
- Suppression ou renommage d’IDs ou classes critiques
- Introduction de dépendances externes (Tailwind CDN, nouvelles polices, etc.)
- Animation lourde ou autoplay
- Dark mode forcé sans token clair (sauf si proposé comme variante explicite)
- Réécriture de la logique de streaming ou de sélection de contexte

## 8. Critères de qualité de la livraison

- Lisibilité excellente sur desktop et mobile
- États clairs en toutes circonstances (erreur, vide, loading, streaming)
- Cohérence totale entre les trois propositions (même structure de tokens)
- Commentaires CSS courts et utiles (pas de bruit)
- Le fichier final reste maintenable par un humain

---

**Instruction pour Grok 4.7** :
Avant d’écrire une seule ligne de CSS, relire intégralement :
1. `design/UI_INVENTORY.md`
2. `static/style.css` (version actuelle)
3. `static/app.js` (tous les endroits qui créent ou lisent des classes/IDs)
4. `templates/coach.html` (structure complète)
5. Le présent `STYLE_BRIEF.md`

Puis proposer les 3 directions sous forme de sections clairement nommées, chacune avec ses tokens + règles + exemples visuels décrits.

Toute modification de style qui violerait la non-régression fonctionnelle sera refusée.
