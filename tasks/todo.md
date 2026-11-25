# DiddiShop — suivi d’implémentation

**Référence :** `IMPLEMENTATION_PLAN.md`  
**Date de démarrage :** 2026-11-24  
**Statut courant :** S0 à S12 terminés localement ; recette staging en attente

> Le dépôt local est initialisé et les lots S0 à S8 sont poussés sur `main`.
> Les seules cases restantes concernent la recette et le provisionnement
> d’infrastructure/contrats staging.

## PHASE 0 — préparation

- [x] P0-A — inventaire du dépôt, plan et commandes de vérification
- [x] P0-B — création des fichiers de suivi
- [x] P0-C — extraction des décisions existantes
- [x] P0-D — questions bloquantes documentées

## BLOCAGE OPÉRATIONNEL

- [x] Dépôt Git initialisé et synchronisé avec GitHub

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
- [x] P6-C — réclamations et décisions, sans release V1
- [x] P6-D — remboursements et réconciliation ; release vendeur reportée en V2

## PHASE 7 — Rewards, communication, support et observabilité

- [x] P7-A — projection campagnes et bénéfices DiddiRewards
- [x] P7-B — conversations métier DiddiComms ; notifications événementielles hors contrat
- [x] P7-C — contexte et cas DiddiSupport
- [x] P7-D — métriques, traces, alertes et audit

## PHASE 8 — DiddiBackoffice et recette

- [x] P8-A — routes admin DiddiShop et commandes idempotentes
- [x] P8-B — audit opérateur, réconciliation et runbook
- [x] P8-C — tests intégration MVP et sécurité S2S
- [x] P8-D — rapport final

## Vérifications de déploiement en attente

- [ ] Provisionner PostgreSQL et Redis dans l’environnement cible.
- [ ] Provisionner les clients/scopes DiddiFreeID pour DiddiShop.
- [ ] Valider le contrat DiddiSend prépayé et sa ventilation XOF.
- [ ] Valider la visibilité des images `diddishop_product_image` dans DiddiFiles.
- [ ] Configurer les URLs S2S et certificats/secrets hors dépôt.
- [ ] Exécuter migrations et tests d’intégration contre les services de staging.

## Idées hors plan

- V2 : séquestration marketplace et release vendeur DiddiPay après contrat dédié.

## SUITE — plan staging à exécuter

Référence : `tasks/plan.md`. DiddiMap est explicitement hors périmètre.

- [x] S0 — retirer DiddiMap et aligner les URLs/configurations HTTPS
- [x] S1 — finaliser la persistance et les workers PostgreSQL/Redis
- [x] S2 — activer DiddiFreeID et les scopes S2S réels
- [x] S3 — brancher DiddiFiles, boutiques, catalogue et médias
- [x] S4 — brancher DiddiPay, checkout et commandes persistantes
- [x] S5 — activer l’expédition DiddiSend prépayée
- [x] S6 — activer annulations, retours, claims et finance
- [x] S7 — brancher Rewards, Comms, Support et Observe
- [x] S8 — finaliser Backoffice, staging et recette MVP
- [x] S9 — activer les tokens DiddiFreeID `client_credentials` par service cible
- [x] S10 — corriger DiddiComms : conversation métier sans notification événementielle
- [x] S11 — aligner DiddiRewards et imposer XOF exclusivement
- [x] S12 — intégrer DiddiObserve OTLP HTTP/protobuf, corrélation et filtrage de confidentialité
- [x] S13 — vérifier les contrats staging, aligner DiddiPay et ajouter le Compose local
- [x] S14 — construire le portail documentaire MkDocs publiable
