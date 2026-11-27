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
- [x] S15 — reproduire la stack Portainer DiddiGo avec API et MkDocs unifiés
- [x] S16 — compléter la surface frontend V1 et formaliser les réponses HTTP
- [x] S17 — intégrer CORS pour les sous-domaines DiddiFree et localhost
- [x] S18 — formaliser les contrats frontend, catégories, médias et schémas OpenAPI
- [x] S19 — déclencher DiddiSend après le signal vendeur « commande prête »
- [x] S20 — auditer la couverture MkDocs des routes, protocoles et valeurs
- [x] S21 — documenter chaque route, payload, contrainte, réponse et limite
- [x] S22 — implémenter les contrats frontend incomplets et leur idempotence
- [x] S23-A — fixer exactement la quantité d’une ligne panier
- [x] S23-B — fermer le contrat DiddiPay et l’historique/pagination commandes
- [x] S23-C — fermer le contrat réclamations, preuves et remboursements
- [x] S23-D — normaliser le contrat de suivi DiddiSend
- [x] S24-A — transmettre toutes les variables d’exécution au Compose Portainer
- [x] S24-B — rendre docker-compose.yml canonique pour Portainer et isoler le local
- [x] S24-C — aligner le webhook DiddiPay sur le contrat PAYMENT_CALLBACK_TARGETS
- [x] S24-D — aligner les scopes DiddiSend et isoler le blocage d’auth staging
- [x] S24-E — corriger la validation JWT/JWKS dans l’image API
- [x] S24-F — aligner les JWT utilisateurs sans audience et rendre l’issuer obligatoire
- [x] S24-G — exécuter automatiquement les migrations Alembic avant l’API staging
- [x] S24-H — réhydrater le statut produit enum depuis PostgreSQL
- [x] S24-I — normaliser le devis DiddiSend et mapper les erreurs upstream
- [x] S24-J — aligner le payload PaymentIntent sur DiddiPay staging
- [x] S24-K — persister les échecs PaymentIntent et autoriser le retry
- [x] S24-L — transmettre customer_phone à DiddiPay/PawaPay
- [x] S24-M — réconcilier les anciens checkouts pending avec paiement failed
- [x] S24-N — verrouiller customer_phone, tester routes/SQL/HTTP et identifier les rejeux
- [x] S24-O — transmettre le retour Payment Page, reprendre les anciens checkouts et exposer next_action
- [x] S24-P — réhydrater les statuts SQL et valider webhook → vendeur → livraison sur PostgreSQL Docker
- [x] S24-Q — transmettre les coordonnées obligatoires du sender DiddiSend
- [x] S24-R — fermer la première vague de contrats frontend
- [x] S24-S — fermer remboursements et preuves photo
- [x] S24-T — normaliser claims et suivi coursier
- [x] S24-U — exposer destination et ETA de livraison sans inventer de données
- [x] S24-V — réhydrater les coordonnées sender pour les anciennes commandes
- [x] S24-W — transmettre la référence PaymentIntent aux livraisons prépayées
- [x] S24-X — mapper les refus DiddiSend et documenter la visibilité inter-client DiddiPay
- [x] S24-Y — aligner order_reference sur business_reference pour verify coverage
