# DiddiShop — plan d’implémentation de la suite

**Date :** 2026-11-24  
**Base :** `IMPLEMENTATION_PLAN.md`, `CAPABILITY-MAP.md`, contrats de staging
observés et décision D-016  
**Statut :** à exécuter après validation du cadrage

## 1. État de départ

Le dépôt contient un monolithe modulaire Clean Architecture, les frontières de
modules, les ports S2S, les événements, l’idempotence et des faux adaptateurs
testés. La suite ne doit pas recréer le squelette : elle doit remplacer les
stubs par des implémentations persistantes et des raccordements staging
vérifiables.

La livraison est entièrement déléguée à DiddiSend. DiddiShop ne dépend pas de
DiddiMap et ne valide pas ou ne géocode pas lui-même les adresses.

## 2. URLs staging de référence

Les URLs de documentation servent à comprendre les contrats ; elles ne sont
pas les URLs appelées par DiddiShop.

| Intégration | Base runtime à configurer | Vérification connue |
|---|---|---|
| DiddiFreeID | `https://auth-staging.diddifree.com` | `/.well-known/jwks.json` |
| DiddiPay | `https://pay-api-staging.diddifree.com/payfund/v1` | `/health` |
| DiddiSend | `https://diddisend-api-staging.diddifree.com` | `/health`, `/openapi.json` |
| DiddiFiles API | `https://diddifiles.diddifree.com` | `/openapi.json` |
| DiddiFiles S3 | `https://s3.diddifiles.diddifree.com` | endpoint S3, pas une page web |
| DiddiRewards | `https://diddi-rewards-staging.diddifree.com` | `/health`, `/openapi.json` |
| DiddiComms | `https://diddi-comm-staging.diddifree.com` | `/health` |
| DiddiSupport | `https://support-backend-staging.diddifree.com` | contrat à confirmer |
| DiddiObserve | `https://logs-otel.diddifree.com` | OTLP ; backend à rétablir après `502` |
| DiddiBackoffice | `https://admin-staging.diddifree.com` | interface opérateur, pas une base DiddiShop |

Documentation utile : DiddiFood, DiddiSend, DiddiComms et DiddiRewards. Les
URLs en `http` fournies initialement ne doivent pas être utilisées pour les
secrets, les JWT ou les payloads métier.

## 3. Ordre d’implémentation

```text
S0 — Nettoyage de frontière et configuration
 ↓
S1 — Persistance réelle et workers PostgreSQL/Redis
 ↓
S2 — Authentification réelle DiddiFreeID et scopes S2S
 ↓
S3 — DiddiFiles + boutiques + catalogue + médias
 ↓
S4 — Checkout, paiement DiddiPay et commandes
 ↓
S5 — Expédition DiddiSend et suivi
 ↓
S6 — Annulations, retours, réclamations et finance
 ↓
S7 — Rewards, Comms, Support et Observe
 ↓
S8 — Backoffice, tests staging et recette MVP
```

## 4. Lots détaillés

### S0 — Nettoyage de frontière et configuration

**Objectif :** aligner le dépôt sur le périmètre confirmé avant tout nouveau
code métier.

- supprimer `DiddiMapAdapter`, `diddimap_base_url` et son enregistrement DI ;
- supprimer `LocationPort` et toute référence documentaire à DiddiMap ;
- conserver dans `DeliveryPort` les adresses et coordonnées nécessaires à
  DiddiSend, sans validation locale ;
- ajouter les variables d’environnement HTTPS et les préfixes de chemin ;
- ajouter un contrôle de démarrage qui refuse une URL vide pour une intégration
  activée ;
- documenter les routes de santé et OpenAPI séparément des routes métier.

**Acceptation :** aucun import, setting, port ou document DiddiShop ne référence
DiddiMap ; le démarrage charge les bases DiddiPay, DiddiSend, DiddiFiles,
DiddiRewards, DiddiComms, DiddiSupport et DiddiObserve depuis l’environnement.

**Vérification :** tests d’architecture, compilation, lint et test de chargement
de configuration sans secret committé.

### S1 — Persistance réelle et workers PostgreSQL/Redis

**Objectif :** rendre les invariants transactionnels exécutables.

- finaliser les modèles PostgreSQL et migrations pour shops, catalog, cart,
  orders, claims, financial snapshots, audit, outbox et inbox ;
- implémenter les repositories sans lecture de tables d’un autre module ;
- utiliser PostgreSQL pour l’état métier et Redis pour verrous, files et
  coordination des workers ;
- implémenter le worker outbox avec retry borné, backoff, visibilité et DLQ ;
- implémenter l’inbox avec déduplication par consommateur et `event_id` ;
- conserver les transitions et événements dans une même transaction.

**Acceptation :** un crash après commit métier n’efface pas l’événement ; un
retry worker ou webhook ne crée jamais un deuxième effet métier.

**Vérification :** migrations, tests transactionnels, tests de concurrence,
tests de doublons et tests avec PostgreSQL/Redis de staging ou conteneurisés.

### S2 — Authentification réelle et scopes S2S

**Objectif :** sécuriser les appels interservices.

- valider les JWT utilisateur via JWKS DiddiFreeID ;
- distinguer utilisateur, vendeur, support, admin et service S2S ;
- créer des credentials/scopes dédiés par service ;
- propager `X-Request-ID`, `traceparent`, `X-Origin-Service` et les identifiants
  métier requis ;
- refuser les secrets absents en staging ;
- journaliser uniquement les métadonnées non sensibles.

**Acceptation :** un token DiddiPay ne peut pas appeler DiddiSend ; les routes
vendeur vérifient la boutique ; les webhooks externes sont authentifiés et
rejouables sans duplication.

**Vérification :** tests de scopes, audience, expiration, JWKS, permissions et
absence de secret dans les logs.

### S3 — DiddiFiles, boutiques, catalogue et médias

**Objectif :** rendre les produits physiques publiables et consultables.

- implémenter upload/confirmation et URL signée via DiddiFiles ;
- confirmer le purpose `diddishop_product_image` ;
- implémenter boutiques, membres, suspension et permissions vendeur ;
- implémenter produits, catégories, prix XAF, publication et stock ;
- ne conserver dans DiddiShop que les références et snapshots nécessaires ;
- décrémenter et restituer le stock de façon atomique et idempotente.

**Acceptation :** une image privée n’est jamais exposée par erreur ; deux
checkouts concurrents ne vendent pas le dernier stock ; un prix déjà commandé
reste inchangé après modification du catalogue.

**Vérification :** tests API vendeur/client, concurrence stock et contrat
DiddiFiles.

### S4 — Checkout, DiddiPay et commandes

**Objectif :** créer un checkout multi-boutiques payable et traçable.

- panier multi-boutiques et création d’une commande par boutique ;
- snapshot des prix, frais DiddiSend, commission et avantages Rewards ;
- appel PaymentIntent sur DiddiPay avec clé stable ;
- réception et déduplication des événements paiement ;
- machine d’états séparant `fulfillment_status` et `payment_status` ;
- gestion explicite de `pending`, `processing`, `succeeded`, `failed` et
  `refunded` ;
- ne jamais transmettre de données carte à DiddiShop.

**Acceptation :** un checkout de trois boutiques possède un paiement et trois
commandes cohérentes ; une réponse DiddiPay inconnue reste reprenable ; un
webhook confirmé est idempotent.

**Vérification :** contrat DiddiPay, webhooks signés, paiement échoué,
rejeu, timeout et concurrence checkout.

### S5 — Expédition DiddiSend

**Objectif :** expédier sans second débit et sans dépendance à la flotte.

- aligner le payload sur le contrat DiddiFood/DiddiSend ;
- envoyer `origin_module=diddishop`, `order_reference`, adresses, colis,
  `quoted_price`, `financial_breakdown`, `payment_method=diddipay` et
  `prepaid_by_origin=true` ;
- utiliser un credential S2S DiddiShop et une clé stable ;
- demander à DiddiSend le devis puis créer la livraison après confirmation
  paiement et préparation vendeur ;
- persister `delivery_id` et le devis ;
- consommer `delivery.created`, `picked_up`, `in_transit`, `delivered`,
  `failed` et `returned` ;
- traiter les erreurs d’adresse renvoyées par DiddiSend sans appeler DiddiMap ;
- annuler côté DiddiSend uniquement lorsque l’état logistique l’autorise.

**Acceptation :** DiddiSend ne crée pas de second PaymentIntent ; un retry de
création renvoie la même livraison ; une livraison reste la source de vérité
de son statut opérationnel.

**Vérification :** OpenAPI DiddiSend, test `prepaid_by_origin`, retry réseau,
événements dupliqués, échec de remise et retour à l’expéditeur.

### S6 — Finance, annulations, retours et réclamations

**Objectif :** appliquer la matrice financière déjà définie.

- expiration confirmation vendeur ;
- annulation avant prise en charge ;
- remboursement total/partiel avec clé d’opération ;
- fenêtre de réclamation de 72 heures ;
- blocage de release dès ouverture d’une réclamation ;
- libération vendeur après délai et absence de litige ;
- garder la release derrière le contrat marketplace DiddiPay ;
- distinguer décision locale, demande externe et confirmation financière ;
- auditer les décisions support et les corrections.

**Acceptation :** aucune libération sans vérification de l’absence de litige ;
un remboursement confirmé est nécessaire avant le statut financier final ;
chaque opération peut être réconciliée avec DiddiPay.

**Vérification :** annulations concurrentes, refunds partiels, réclamation à
la limite de la fenêtre, timeout DiddiPay et réconciliation.

### S7 — Rewards, Comms, Support et Observe

**Objectif :** brancher les services transverses sans déplacer la propriété
métier.

- DiddiRewards : quote/reserve/confirm/correct ou release selon le contrat
  réel, avec snapshot de campagne/version ;
- Redis Streams Rewards : outbox producteur et inbox consommateur après commit ;
- DiddiComms : tâches dérivées des événements avec retry et déduplication ;
- DiddiSupport : contexte agrégé, ouverture de cas et décision idempotente ;
- DiddiObserve : export OTLP/logs/métriques/traces et corrélation ;
- aucune notification ou panne d’observabilité ne doit modifier la commande.

**Acceptation :** Rewards reste propriétaire du ledger, Comms du transport des
messages, Support de ses dossiers et Observe de la télémétrie.

**Vérification :** contrats HTTP/Redis, retries, DLQ, absence de données
sensibles, tests avec les endpoints de staging et résolution du `502` Observe.

### S8 — Backoffice et recette staging

**Objectif :** rendre le MVP opérable et validable de bout en bout.

- routes DiddiShop consommées par DiddiBackoffice ;
- commandes sensibles avec acteur, motif, corrélation et idempotence ;
- audit local et traçabilité externe ;
- dashboards et alertes opérationnels ;
- runbook de réconciliation paiement/livraison ;
- recette des 15 scénarios MVP déjà listés dans `IMPLEMENTATION_PLAN.md` ;
- vérification des migrations, workers, scopes, secrets et certificats.

**Acceptation :** aucun accès direct du backoffice aux tables DiddiShop ; les
scénarios achat, livraison, remboursement, réclamation et release sont
rejouables et auditables.

## 5. Dépendances et parallélisation

### Séquentiel obligatoire

`S0 → S1 → S2 → S4 → S5 → S6 → S8`

### En parallèle après S2

- S3 boutiques/catalogue/DiddiFiles ;
- S7 Rewards/Comms/Support/Observe, avec contrats mockés au départ.

### Blocages externes à traiter tôt

1. contrat marketplace DiddiPay : hold/refund partiel/release vendeur ;
2. contrat DiddiSend : `prepaid_by_origin=true` et événements signés ;
3. contrat DiddiFiles : URL signée et purpose produit ;
4. scopes S2S DiddiFreeID par service ;
5. endpoint et protocole DiddiObserve ;
6. route et enveloppe DiddiSupport.

## 6. Règle de livraison par lot

Chaque lot doit livrer : code domaine/application/infrastructure/API, tests,
migration éventuelle, contrat documenté, journal de phase, commit dédié et
vérification locale. Aucun lot ne doit introduire DiddiMap ou un appel direct
à la flotte, au ledger Rewards, à la comptabilité Pay ou aux bases externes.

## 7. Première tranche à exécuter

Commencer par **S0-A à S0-C** :

1. retirer DiddiMap du registre d’intégrations et des settings ;
2. configurer les bases HTTPS et les préfixes DiddiPay/DiddiSend ;
3. ajouter les tests de configuration et d’architecture ;
4. mettre à jour le contrat DiddiSend pour confirmer que la validation
   opérationnelle est de sa responsabilité.

La première tranche ne doit pas encore activer les remboursements réels, la
release vendeur ou les workers de production tant que leurs contrats externes
ne sont pas confirmés.
