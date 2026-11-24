# MISSION : IMPLÉMENTER LE PLAN EN ENTIER, EN AUTONOMIE

PLAN À IMPLÉMENTER : IMPLEMENTATION_PLAN.md
MAP DU PROJET: [text](INTEGRATION_MAP.md)

Ta mission est d'implémenter TOUT ce plan, phase après phase, jusqu'au bout.
Tu fonctionnes en deux temps : PHASE 0 (préparation + questions, une seule fois),
puis BOUCLE AUTONOME (sans questions, sans t'arrêter).

## 1. Fichiers de suivi
Si le projet a déjà ses conventions (dossiers `tasks/`, `docs/`, nommage des fichiers), suis-les.
Sinon, crée :
- `tasks/todo.md` : liste de toutes les phases et sous-lots avec cases à cocher. C'est TA mémoire, il fait foi.
- `docs/IMPLEMENTATION-STATUS.md` : état global + section « Vérifications de déploiement en attente ».
- `docs/decisions/DECISIONS.md` : toutes les décisions (format en section 4).
- `tasks/PHASE-X-PLAN-AAAA-MM-JJ.md` : découpage de chaque phase.
- `tasks/PHASE-XY-IMPLEMENTATION-AAAA-MM-JJ.md` : journal de chaque sous-lot.

Si tu redémarres ou si ton contexte a été résumé : relis `tasks/todo.md`,
`DECISIONS.md` et `git log --oneline -20` avant de faire quoi que ce soit.

## 2. PHASE 0 : préparation et questions (une seule fois)
1. Lis le plan, les documents d'architecture, le code existant, `git status`, `git log`.
2. Repère les commandes de vérification du projet (lint, compilation, tests, migrations)
   et note-les dans `docs/IMPLEMENTATION-STATUS.md`.
3. Crée les fichiers de suivi manquants. Remplis `tasks/todo.md` avec toutes les phases du plan.
4. Extrais dans `DECISIONS.md` toutes les décisions DÉJÀ prises dans le plan et les docs,
   avec leur source (fichier et section).
5. Liste tes questions dans `tasks/QUESTIONS-<date>.md`, avec ces règles :
   - seulement celles où une mauvaise supposition coûterait cher (contrat avec un autre
     service, règle d'argent, modèle de données, sécurité, contradiction entre documents) ;
   - 7 questions maximum, regroupées dans un seul message ;
   - pour chaque question : le contexte en une ligne, 2 ou 3 options et ton option recommandée.
6. Affiche les questions et ARRÊTE-TOI. Attends mes réponses.
   S'il n'y a aucune question utile, dis-le et passe directement à la boucle.
7. Quand je réponds : écris chaque réponse dans `DECISIONS.md` (source : « Utilisateur »),
   fais un commit et un push des documents, puis lance la boucle. À partir de là, tu ne poses plus de questions.

## 3. BOUCLE AUTONOME
Pour chaque PHASE du plan, dans l'ordre :
1. Relis le plan, `DECISIONS.md` et les modules de code concernés.
2. Découpe la phase en sous-lots (A, B, C…), chacun livrable et testable seul.
3. Écris `tasks/PHASE-X-PLAN-<date>.md`.

Pour chaque SOUS-LOT :
4. Implémente en Clean Architecture : domaine → application → infrastructure →
   présentation/API → tests.
5. Ajoute les migrations si nécessaire.
6. Ajoute les contrats S2S (service à service), les événements, l'idempotence, les logs et le traçage.
7. Lance toutes les commandes de vérification notées en Phase 0. Si un outil est
   indisponible (ex. PostgreSQL, Redis), note-le dans le journal et continue.
8. Mets à jour le journal du sous-lot, `tasks/todo.md`, `docs/IMPLEMENTATION-STATUS.md`,
   `DECISIONS.md` et la doc des contrats/protocoles si elle existe.
9. Fais un commit dédié au sous-lot (convention visible dans `git log`), puis pousse sur la branche actuelle.
10. Ne vérifie pas le déploiement. Ajoute ce qu'il faudra vérifier dans
    « Vérifications de déploiement en attente ».
11. Passe IMMÉDIATEMENT au sous-lot suivant. Ne t'arrête pas pour faire un résumé.

## 4. Décisions : toujours les sauvegarder
Chaque choix non trivial va dans `DECISIONS.md`, au moment où tu le fais :

```
### D-<numéro> — <titre court>
- Date : AAAA-MM-JJ
- Phase / sous-lot : <ex. P3-B>
- Décision : <ce qui a été choisi>
- Pourquoi : <une ou deux lignes>
- Alternatives écartées : <liste courte>
- Source : Plan | Utilisateur | Agent (à valider)
- Impact : <modules concernés>
```

Une décision existante ne se modifie jamais en silence. Si tu dois en changer une,
crée une nouvelle décision qui la remplace et indique « remplace D-xx ».

## 5. En cas de blocage : documenter et continuer
- Test en échec : cherche la cause racine. Fais au maximum 3 tentatives.
  Il est INTERDIT de désactiver ou d'affaiblir un test.
- Après 3 échecs : pousse le code partiel sur `wip/<phase-sous-lot>`, reviens sur la branche
  actuelle, marque le sous-lot « BLOQUÉ » dans `todo.md` avec la raison, détaille dans le journal, continue.
- Ne pousse jamais de code dont les tests échouent sur la branche actuelle.
- Si une décision manque : prends l'option la plus prudente et la plus réversible, enregistre-la
  (Source : Agent, à valider) et continue.
- Si un service externe n'est pas prêt ou si son contrat est flou : code contre une interface
  (port) avec un faux adaptateur testé, écris le contrat attendu dans la doc des contrats,
  marque-le « contrat à valider » et continue.
- Si un sous-lot dépend d'un sous-lot BLOQUÉ : marque-le « EN ATTENTE de XY » et passe à la suite indépendante.

## 6. Interdits
- Pas de `git push --force`, pas de réécriture d'historique, pas de `reset --hard` sur du travail poussé.
- Pas de secret, de token ni de `.env` dans les commits.
- Pas de migration destructive sans retour arrière (downgrade).
- Rien en dehors du plan. Les idées vont dans `todo.md` sous « Idées hors plan », sans les implémenter.

## 7. Condition de fin (vérifie-la après CHAQUE sous-lot)
Le plan est terminé seulement si :
- toutes les phases du plan sont marquées terminées dans `todo.md` et `IMPLEMENTATION-STATUS.md` ;
- il ne reste aucune case `- [ ]`, en dehors des éléments BLOQUÉ, EN ATTENTE et des vérifications de déploiement ;
- toutes les vérifications passent sur la branche actuelle ;
- tout est commité et poussé.

Si une seule condition est fausse, reprends la boucle au prochain sous-lot.

## 8. Rapport final (seulement quand la condition de fin est vraie)
Écris `tasks/RAPPORT-FINAL-<date>.md` et affiche-le, en restant court :
- phases et sous-lots terminés, avec les hash de commit ;
- éléments BLOQUÉ et EN ATTENTE, avec la raison et la branche `wip/` ;
- décisions « Agent, à valider » ;
- contrats « à valider » avec les autres services ;
- vérifications de déploiement à faire ;
- ce qui n'a pas pu être testé.

Commence par la PHASE 0.