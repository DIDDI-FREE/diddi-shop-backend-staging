# DiddiShop — Carte des capacités et frontières

**Version :** 0.1  
**Statut :** carte appliquée au squelette backend initial

Le code initial est placé sous `app_base/` pour reprendre la convention observée
dans une composition centrale (`core/deps.py`, `main.py`). Les capacités
fonctionnelles restent volontairement incomplètes ; cette carte définit les
frontières avant l’implémentation verticale des use cases.

Ce document fixe les modules internes de DiddiShop, leurs responsabilités et leur direction de dépendance. Les services externes restent hors du dépôt et sont consommés uniquement par des adaptateurs.

## 1. Principe d'architecture

DiddiShop est un monolithe modulaire Clean Architecture : un seul déploiement au départ, mais des métiers séparés par des ports, des use cases et des modèles propres.

```text
HTTP / Webhooks / Workers
          ↓
Presentation adapters
          ↓
Application use cases
          ↓
Domain entities + policies
          ↓
Ports
          ↓
Infrastructure adapters
```

Règles obligatoires :

- un module métier ne lit jamais les tables d'un autre module ;
- les échanges internes passent par un use case, un port ou un événement ;
- le domaine ne connaît ni FastAPI, ni SQLAlchemy, ni Redis, ni HTTP ;
- les services externes ne sont jamais appelés directement depuis le domaine ;
- les montants, références de fichiers et identifiants externes sont copiés comme snapshots lorsque l'historique métier l'exige ;
- les événements sortants passent par une outbox et les événements entrants par une inbox dédupliquée ;
- la livraison passe exclusivement par DiddiSend ; aucun module Shop ne connaît la flotte.

## 2. Carte des capacités

Les identifiants sont stables et seront utilisés dans les specs, tickets et dossiers.

| Module id | Responsabilité | Possède | Dépend de |
| --- | --- | --- | --- |
| `platform-runtime` | Base technique commune minimale | configuration, DB session, migrations, outbox, inbox, clock, idempotence | — |
| `observability` | Logs, traces, métriques, corrélation et alertes | conventions de télémétrie DiddiShop | `platform-runtime` |
| `identity-access` | Vérification du JWT et autorisation locale | contexte utilisateur, rôles boutique, politiques d'accès | `platform-runtime`, `observability` |
| `external-integrations` | Ports et adaptateurs vers les services Diddi | clients DiddiPay, DiddiSend, DiddiFiles, DiddiMap, Notifications | `platform-runtime`, `identity-access`, `observability` |
| `shops` | Boutique, profil vendeur, membres et suspension | boutiques et autorisations boutique | `platform-runtime`, `identity-access`, `external-integrations` |
| `catalog` | Catégories, articles physiques, stock et médias | catalogue, stock, statuts de publication | `shops`, `external-integrations` |
| `cart` | Panier et lignes de panier | panier acheteur, lignes et quantités | `catalog`, `shops`, `identity-access` |
| `checkout-orders` | Validation, commandes, transitions et snapshots financiers | checkout, commandes, lignes figées, historique de statut | `cart`, `catalog`, `shops`, `external-integrations` |
| `claims` | Réclamations et décisions financières métier | réclamations, preuves, décisions et historique | `checkout-orders`, `external-integrations`, `identity-access` |
| `communication` | Notifications et messages déclenchés par événements | préférences, messages, tentatives et accusés | `checkout-orders`, `claims`, `external-integrations`, `observability` |
| `support` | Opérations support, recherche, décisions et audit | dossiers support, actions opérateur, journal d'audit | `checkout-orders`, `claims`, `shops`, `communication`, `identity-access` |

### Ordre de construction

```text
platform-runtime
        ↓
observability → identity-access → external-integrations
                                      ↓
                         shops → catalog → cart
                                      ↓
                              checkout-orders
                                      ↓
                                  claims
                                      ↓
                          communication → support
```

`observability` est transversal à tous les modules, mais ne doit contenir aucune règle métier. `support` est construit après les parcours opérationnels afin de ne pas devenir une seconde implémentation des commandes ou des réclamations.

## 3. Frontières détaillées

### `platform-runtime`

Contient uniquement les primitives partagées :

- configuration typée par environnement ;
- connexion et transactions PostgreSQL ;
- migrations ;
- horloge injectable ;
- identifiants et corrélation ;
- `Idempotency-Key` HTTP ;
- tables `outbox_events`, `inbox_events`, `processed_commands` ;
- workers et verrous distribués.

Ne contient aucune entité `Shop`, `Product`, `Order` ou `Claim`.

### `observability`

Contrat commun :

- `request_id` dans chaque requête et événement ;
- `traceparent` propagé vers les adaptateurs HTTP et les workers ;
- logs JSON structurés ;
- métriques par module, use case et dépendance externe ;
- durée, statut, retries et erreurs des appels inter-services ;
- aucune donnée sensible : JWT, secret, signature complète, PIN, donnée bancaire ou URL privée.

Métriques initiales :

```text
diddishop_http_requests_total
diddishop_usecase_duration_seconds
diddishop_external_requests_total
diddishop_external_request_duration_seconds
diddishop_outbox_pending
diddishop_inbox_duplicates_total
diddishop_orders_by_status
diddishop_payment_reconciliation_age_seconds
diddishop_support_cases_open
```

### `identity-access`

Responsabilités :

- vérifier localement les JWT DiddiFree ID via JWKS ;
- extraire `user_id`, rôles globaux et état du compte ;
- vérifier les droits vendeur sur une boutique dans DiddiShop ;
- distinguer utilisateur, support, admin et service S2S ;
- ne jamais appeler DiddiFree ID pour valider chaque requête.

Les règles de propriété boutique restent dans `shops`, pas dans un middleware global.

### `external-integrations`

Les interfaces métier sont définies côté application, puis implémentées ici.

Ports principaux :

```text
PaymentPort
  create_payment_intent()
  get_payment_intent()
  request_refund()
  request_seller_release()

DeliveryPort
  quote()
  create_prepaid_delivery()
  get_delivery()
  cancel_delivery()

FilePort
  create_upload_session()
  confirm_upload()
  get_download_url()
  get_public_url()

NotificationPort
  send()

LocationPort
  validate_pickup_address()
```

Les méthodes sont des ports métier. Les détails HTTP, JWT S2S, HMAC, Redis et URLs restent dans les adaptateurs.

### `shops`

Possède :

- profil vendeur local ;
- boutique ;
- membre de boutique ;
- statut active/suspendue ;
- adresse de retrait validée ;
- règles d'accès propriétaire.

Ne possède pas :

- solde vendeur ;
- catalogue article ;
- commande ;
- paiement ;
- fichier binaire.

### `catalog`

Possède :

- catégories à deux niveaux ;
- article physique ;
- stock ;
- statut brouillon/publié/en pause/retiré ;
- références `file_id` DiddiFiles ;
- snapshot des règles de publication.

Le stock est modifié uniquement par des use cases transactionnels et atomiques. Le catalogue ne connaît pas le paiement ou la livraison.

### `cart`

Possède :

- un panier par acheteur ;
- lignes, quantités et date de modification ;
- lecture regroupée par boutique.

Le panier ne réserve pas le stock et ne crée aucun paiement. La validation appartient à `checkout-orders`.

### `checkout-orders`

Possède :

- validation de panier ;
- commandes par boutique ;
- lignes de commande avec prix et titre figés ;
- frais de livraison figés ;
- référence `payment_intent_id` ;
- référence `delivery_id` ;
- machine à états logistique ;
- statut financier ;
- historique append-only ;
- publication des événements de commande.

Ce module est le seul autorisé à orchestrer le parcours commande. Il ne lit jamais directement les bases DiddiPay ou DiddiSend.

### `claims`

Possède :

- réclamation ;
- motif ;
- preuves référencées par `file_id` ;
- fenêtre de 72 heures ;
- décision support ;
- montant demandé et montant décidé ;
- blocage/déblocage de la libération vendeur.

Il demande un remboursement ou une libération via `PaymentPort`, sans calculer la comptabilité DiddiPay.

### `communication`

Réagit aux événements métier :

```text
order.created
order.confirmed
order.cancelled
order.delivered
order.returned
claim.opened
claim.decided
payment.succeeded
payment.refunded
```

Le module ne modifie jamais une commande pour signaler un échec de notification. Il conserve la tentative, applique un retry et expose l'incident au support technique.

### `support`

Possède :

- recherche opérationnelle par commande, boutique, paiement et livraison ;
- dossier support ;
- décision de réclamation ;
- commande administrative idempotente ;
- acteur, justification, corrélation et résultat ;
- audit append-only.

Le support appelle les use cases de `claims`, `checkout-orders` et `shops`. Il ne modifie jamais leurs tables directement.

## 4. Services externes et propriété des données

| Service | Source de vérité | DiddiShop conserve |
| --- | --- | --- |
| DiddiFree ID | identité et JWT | `user_id`, rôles et contexte vérifié |
| DiddiFiles | octets et métadonnées fichier | `file_id`, purpose, statut utile |
| DiddiPay | PaymentIntent, remboursements, argent | références, snapshots financiers et statuts synchronisés |
| DiddiSend | devis, livraison, coursier, preuves | `delivery_id`, statut et événements synchronisés |
| DiddiMap | localités et géocodage | référence d'adresse validée |
| Notifications/DiddiComms | remise des messages | statut de tentative et accusé |

## 5. Squelette de dossiers appliqué

```text
app_base/
├── main.py
├── core/                    # settings, DI, outbox/inbox, observabilité
├── shared_kernel/contracts/ # événements et DTO externes versionnés
├── integrations/            # adaptateurs S2S isolés
├── modules/
│   ├── shops/
│   ├── catalog/
│   ├── cart/
│   ├── checkout/
│   ├── orders/
│   ├── claims/
│   ├── rewards/
│   ├── campaigns/
│   ├── comms/
│   ├── support/
│   ├── observability/
│   ├── audit/
│   └── admin/
└── workers/

tests/
├── unit/
├── integration/
└── contract/

alembic/
docs/
tasks/
```

Chaque module métier suivra la même forme :

```text
module/
├── domain/
├── application/
│   ├── commands.py
│   ├── ports.py
│   └── use_cases.py
├── infrastructure/
└── presentation/
```

## 6. Contrôle de dépendance

Les imports suivants seront interdits par convention et par test d'architecture :

- `domain` vers `infrastructure` ou `presentation` ;
- `catalog` vers `checkout_orders` ;
- `cart` vers `diddipay` ;
- `shops` vers `orders` ;
- `support` vers les repositories d'un autre module ;
- tout module vers la base d'un service externe ;
- tout appel direct de DiddiShop vers un service de flotte ou de coursiers.

## 7. Points à valider avant l’implémentation verticale

1. Le découpage `checkout-orders` est-il accepté comme un seul module pour éviter une dépendance circulaire entre checkout et commande ?
2. DiddiPay expose-t-il, ou doit-il encore exposer, un vrai contrat de séquestre/allocation/libération vendeur ?
3. DiddiSend accepte-t-il un mode de livraison prépayé par DiddiShop sans créer un second paiement ?
4. Les images catalogue DiddiShop doivent-elles être publiques ou rester accessibles par URLs signées ?
5. DiddiShop consommera-t-il les événements DiddiSend via Redis Streams ou via callback HTTP signé ?

## 8. Critère d'acceptation de cette carte

La carte est validée lorsque chaque module a une responsabilité unique, qu'aucune dépendance ne forme de cycle et que les trois contrats bloquants — DiddiPay marketplace, DiddiSend prépayé et DiddiFiles catalogue — ont un propriétaire identifié.
