# DiddiShop — suivi d’implémentation

**Référence :** `IMPLEMENTATION_PLAN.md`  
**Date de démarrage :** 2026-11-24  
**Statut courant :** PHASE 0 terminée, boucle autonome prête à démarrer

> Le dépôt local est initialisé et le commit initial existe. Le push est en
> attente car GitHub répond `Repository not found` sur le remote fourni.

## PHASE 0 — préparation

- [x] P0-A — inventaire du dépôt, plan et commandes de vérification
- [x] P0-B — création des fichiers de suivi
- [x] P0-C — extraction des décisions existantes
- [x] P0-D — questions bloquantes documentées

## BLOCAGE OPÉRATIONNEL

- [ ] Push du commit initial vers GitHub — EN ATTENTE : remote fourni introuvable

## PHASE 1 — fondations techniques

- [x] P1-A — configuration, environnement et gestion d’erreurs
- [x] P1-B — PostgreSQL, transactions et migrations réversibles
- [x] P1-C — outbox, inbox, idempotence et workers
- [x] P1-D — request/correlation/trace context et observabilité de base

## PHASE 2 — identité et intégrations

- [x] P2-A — identité utilisateur et S2S DiddiFreeID
- [x] P2-B — ports et adaptateurs DiddiPay/DiddiSend/DiddiFiles
- [x] P2-C — ports et adaptateurs DiddiRewards/DiddiComms/DiddiSupport/DiddiObserve
- [x] P2-D — tests contractuels et normalisation des erreurs externes

## PHASE 3 — boutiques, catalogue et stock

- [x] P3-A — boutiques, vendeurs et permissions
- [x] P3-B — produits, catégories, publication et médias DiddiFiles
- [x] P3-C — stock atomique et restitution idempotente
- [x] P3-D — API de lecture catalogue

## PHASE 4 — panier, checkout et commandes

- [x] P4-A — panier multi-boutiques
- [x] P4-B — pricing, frais DiddiSend et snapshots financiers
- [x] P4-C — création checkout, commandes par boutique et PaymentIntent
- [x] P4-D — machine à états, historique et événements de commande

## PHASE 5 — paiement confirmé et expédition

- [x] P5-A — webhook DiddiPay et transitions financières
- [x] P5-B — quote/création/annulation DiddiSend
- [x] P5-C — événements de livraison, preuves et suivi

## PHASE 6 — annulations, retours, réclamations et finance

- [x] P6-A — expiration vendeur et annulations
- [x] P6-B — retours, attribution et restitution de stock
- [x] P6-C — réclamations, décisions et blocage de release
- [x] P6-D — remboursements, release vendeur et réconciliation

## PHASE 7 — Rewards, communication, support et observabilité

- [x] P7-A — projection campagnes et bénéfices DiddiRewards
- [x] P7-B — notifications DiddiComms et retries
- [x] P7-C — contexte et cas DiddiSupport
- [x] P7-D — métriques, traces, alertes et audit

## PHASE 8 — DiddiBackoffice et recette

- [ ] P8-A — routes admin DiddiShop et commandes idempotentes
- [ ] P8-B — audit opérateur, réconciliation et runbook
- [ ] P8-C — tests intégration MVP et sécurité S2S
- [ ] P8-D — rapport final

## Vérifications de déploiement en attente

- [ ] Provisionner PostgreSQL et Redis dans l’environnement cible.
- [ ] Provisionner les clients/scopes DiddiFreeID pour DiddiShop.
- [ ] Valider les contrats DiddiPay marketplace et DiddiSend prépayé.
- [ ] Valider la visibilité des images `diddishop_product_image` dans DiddiFiles.
- [ ] Configurer les URLs S2S et certificats/secrets hors dépôt.
- [ ] Exécuter migrations et tests d’intégration contre les services de staging.

## Idées hors plan

- Aucune pour le moment.
