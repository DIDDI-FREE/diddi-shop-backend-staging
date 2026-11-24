# DiddiShop — état d’implémentation

**Date :** 2026-11-24  
**Phase courante :** S0 terminé, S1 en préparation  
**Statut :** squelette initial vérifié ; raccordement staging en cours

## État global

Le squelette Clean Architecture existe sous `app_base/`. Les frontières sont
définies pour boutiques, catalogue, panier, checkout, commandes, réclamations,
Rewards/campagnes, communication, support, observabilité, audit et backoffice.

La seule frontière logistique de DiddiShop est DiddiSend. DiddiShop ne dépend
pas d’un service de flotte ou de coursiers.

La logique métier de production n’est pas encore implémentée : les repositories
et adaptateurs actuels constituent un socle de contrats et certains stubs.

## Commandes de vérification identifiées

| Commande | Usage | État |
| --- | --- | --- |
| `python -m compileall -q app_base tests` | compilation Python | disponible |
| `pytest -q` | tests unitaires/squelette | disponible, dernier résultat : 22 passed |
| `ruff check .` | lint | disponible, dernier résultat : OK |
| `alembic upgrade head` | migrations | à exécuter avec PostgreSQL staging |
| tests PostgreSQL/Redis | intégration | indisponibles : infrastructure non configurée |

## Phase 0 réalisée

- plan et documents d’architecture lus ;
- dépôt inspecté ;
- dépôt Git local initialisé et synchronisé avec le remote GitHub ;
- fichiers de suivi créés ;
- décisions existantes extraites ;
- questions bloquantes regroupées dans `tasks/QUESTIONS-2026-11-24.md`.

## Blocages et contrats à valider

1. DiddiPay : hold, remboursement partiel et release vendeur marketplace.
2. DiddiSend : création d’une livraison déjà payée par DiddiShop, sans second
   PaymentIntent.
3. DiddiFiles : URL signée ou publique pour `diddishop_product_image`.
4. DiddiFreeID : clients et scopes S2S DiddiShop.
5. Git : dépôt local à initialiser et remote fourni par l’utilisateur.

## S0 réalisé

- DiddiMap retiré du registre et de la configuration.
- URLs HTTPS staging documentées dans `.env.example`.
- Configuration non développement fail-closed sur les URLs externes.
- Initialisation de l’outbox corrigée.

## Réponses intégrées

- release vendeur : port abstrait, faux adaptateur, contrat réel à valider ;
- expédition : modèle DiddiFood adapté à `origin_module=diddishop` ;
- infrastructure : PostgreSQL + Redis ;
- S2S : scopes dédiés par service ;
- Git : initialisation locale et remote GitHub fourni.

## Vérifications de déploiement en attente

- aucune vérification de déploiement n’a été exécutée conformément à la mission ;
- provisionnement PostgreSQL/Redis ;
- migrations sur staging ;
- configuration des credentials S2S ;
- tests de bout en bout avec DiddiPay, DiddiSend, DiddiFiles et DiddiRewards ;
- vérification des workers outbox/inbox et des alertes.
