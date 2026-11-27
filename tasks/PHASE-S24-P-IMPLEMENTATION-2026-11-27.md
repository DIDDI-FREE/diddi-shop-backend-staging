# S24-P — webhook SQL et parcours vendeur/livraison

## Preuves et causes

- Rapport externe lu uniquement : `diddifree-test/reports/diddishop-e2e-2026-11-27-followup.md`.
  La correspondance individuelle du webhook à la dernière tentative n'est pas
  déduite de ce rapport ; le défaut de sauvegarde est reproduit localement.
- Baseline : 5 échecs / 1 succès sur les nouveaux tests. `.value` sur chaîne,
  webhook 500, faux 404 contenant `ShopService.get` absent, statut boutique str.
- Une relecture supplémentaire dans OrderService.transition perdait la mise à
  jour HELD et la consommation Rewards. Les tests mémoire masquaient ce défaut
  en retournant la même instance ; les repositories SQL créent une nouvelle copie.
- Même perte d'instance à la livraison : sauvegarde des dates avec une version
  antérieure après transition, conduisant à un conflit SQL. Instance actualisée.
- Un essai intermédiaire avait omis `source_service` dans le callback DiddiSend
  de test : fixture alignée au schéma sans affaiblir aucune assertion.

## Corrections et garanties testées

- Reconstruction explicite des enums Order, Shop et DeliveryProjection. Rejet
  des valeurs inconnues, aucun fallback modifiant un état financier.
- Transition sur l'agrégat chargé/modifié ; mêmes enums et même API publique.
- ShopService.get pour les autorisations existantes, get_public conservé.
- Suppression des catch-all masquant 403 et erreurs runtime en faux 404/409.
- Livraison : garder l'agrégat retourné par transition et les dates initiales.
- Webhook signé en environnement test staging, SQL réel avec sessions distinctes,
  inbox/outbox persistantes ; aucune intégration extérieure n'est appelée.
- Un callback déjà traité ne répète pas la transition ; échec avant sauvegarde
  puis même événement récupérable ; reprise après échec de la deuxième commande
  sans répéter la transition de la première. Ces tests sont séquentiels et ne
  prétendent pas démontrer une atomicité globale ou la concurrence distribuée.
- Réhydratation testée pour tous les couples des enums commande/paiement.

## Vérifications

- Suite hôte : 238 passed (2 avertissements de dépréciation existants), Ruff OK.
- Suite Docker Python 3.12 : 238 passed, réseau désactivé ; Ruff Linux OK.
- PostgreSQL 16 Docker jetable : parcours complet signé → lecture SQL →
  confirm/ready → événements livraison → DELIVERED, 1 passed. Réseau interne
  sans sortie, aucun port exposé, données sur tmpfs ; conteneur/réseau supprimés.
- Compilation, MkDocs strict et génération SQL Alembic : OK.
- Pas de migration requise : les données JSON existantes restent compatibles.

Reproduction Docker : construire `Dockerfile.test` en
`diddishop-webhook-tests:local`, puis lancer `docker run --rm --network none`
pour la suite. Pour le test PostgreSQL, utiliser un conteneur 16-alpine neuf
sur un réseau interne avec alias `diddishop-webhook-test-db`, base `diddishop_test`
et identifiants locaux synthétiques `shop_test`/`shop_test`. Exécuter uniquement
`tests/test_payment_webhook_sql.py::test_signed_success_sql_readback_seller_and_delivery_lifecycle`
avec `DIDDI_SHOP_TEST_DATABASE_URL` égal à la constante de test autorisée dans
ce fichier. La fixture refuse toute autre URL ; pas de connexion staging.
Les acteurs API sont injectés dans les tests, pas des sessions DiddiFreeID réelles.

## Reprise distante

Pas de mutation, déploiement ni redéploiement Portainer. Pas de webhook artificiel
en staging et pas de nouveau paiement. Après déploiement manuel utilisateur,
faire reprendre par Pay la notification authentique du PaymentIntent confirmé,
puis lire checkout/commande/vendeur/livraison. Procédure dans le runbook MkDocs.
Le skill Diddi Portainer Ops a guidé la délimitation des opérations et le suivi
documentaire. Aucun fichier d'un autre dépôt n'a été modifié.
