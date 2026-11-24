# DiddiShop — état d’implémentation

**Date :** 2026-11-24  
**Phase courante :** S8 terminé localement
**Statut :** implémentation locale complète ; recette staging en attente

## État global

Le squelette Clean Architecture existe sous `app_base/`. Les frontières sont
définies pour boutiques, catalogue, panier, checkout, commandes, réclamations,
Rewards/campagnes, communication, support, observabilité, audit et backoffice.

La seule frontière logistique de DiddiShop est DiddiSend. DiddiShop ne dépend
pas d’un service de flotte ou de coursiers.

Les phases S0 à S8 sont implémentées localement : persistance SQL, workers
outbox/inbox, authentification, contrats S2S, checkout, paiements, expédition,
finance, transverse et backoffice. Les opérations financières externes qui
dépendent d’un contrat marketplace non confirmé restent protégées derrière
leurs ports.

## Commandes de vérification identifiées

| Commande | Usage | État |
| --- | --- | --- |
| `python -m compileall -q app_base tests alembic` | compilation Python | disponible, OK |
| `pytest -q` | tests unitaires et contrats | disponible, dernier résultat : 39 passed |
| `ruff check .` | lint | disponible, dernier résultat : OK |
| `alembic upgrade head --sql` | vérification des migrations | disponible, OK |
| `alembic upgrade head` | migrations réelles | à exécuter avec PostgreSQL staging |
| tests PostgreSQL/Redis | intégration | indisponibles : infrastructure non configurée |

## Phases S0 à S8 réalisées

- plan et documents d’architecture lus ;
- dépôt inspecté ;
- dépôt Git local initialisé et synchronisé avec le remote GitHub ;
- fichiers de suivi créés ;
- décisions existantes extraites ;
- questions initiales et décisions intégrées dans `docs/decisions/DECISIONS.md`.
- journaux et plans de lots conservés dans `tasks/`.

## Blocages et contrats à valider

1. DiddiPay : hold, remboursement partiel et release vendeur marketplace.
2. DiddiSend : confirmation du mode prépayé et de la ventilation financière
   XAF pour DiddiShop ; le schéma staging observé est orienté Food/XOF.
3. DiddiFiles : visibilité et URL finale des images
   `diddishop_product_image`.
4. DiddiFreeID : provisionnement des clients et scopes S2S.
5. DiddiObserve : endpoint d’ingestion à rétablir ; l’URL observée répondait
   `502`.

## S0 réalisé

- DiddiMap retiré du registre et de la configuration.
- URLs HTTPS staging documentées dans `.env.example`.
- Configuration non développement fail-closed sur les URLs externes.
- Initialisation de l’outbox corrigée.

## Réalisations S1 à S8

- PostgreSQL/Alembic pour les agrégats métier, inbox, outbox, idempotence et audit ; Redis pour la publication et la coordination des workers.
- JWT/JWKS DiddiFreeID, scopes S2S dédiés et signatures HMAC des webhooks.
- DiddiFiles pour les sessions d’upload, confirmation, métadonnées et URLs.
- Checkout multi-boutiques, snapshots de prix, PaymentIntent DiddiPay et machine d’états commande/paiement.
- DiddiSend comme unique propriétaire de l’expédition, avec livraison prépayée et suivi persistant.
- Annulations, retours, réclamations, refunds idempotents et protection de la release vendeur.
- DiddiRewards, DiddiComms, DiddiSupport, DiddiObserve et DiddiBackoffice avec frontières, audit et idempotence.

## Réponses intégrées

- release vendeur : port abstrait, faux adaptateur, contrat réel à valider ;
- expédition : modèle DiddiFood adapté à `origin_module=diddishop` ;
- infrastructure : PostgreSQL + Redis ;
- S2S : scopes dédiés par service ;
- Git : initialisation locale et remote GitHub fourni.

## Vérifications de déploiement en attente

- provisionnement PostgreSQL/Redis ;
- migrations sur staging ;
- configuration des credentials et scopes S2S ;
- tests de bout en bout avec DiddiPay, DiddiSend, DiddiFiles et DiddiRewards ;
- vérification des workers outbox/inbox, DLQ et alertes ;
- validation du contrat marketplace DiddiPay et de la ventilation XAF DiddiSend ;
- rétablissement puis vérification de DiddiObserve.
