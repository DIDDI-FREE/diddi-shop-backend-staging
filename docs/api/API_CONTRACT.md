# Contrat API DiddiShop — HTTP et webhooks

Version documentaire : `draft.2026-11-25`. Périmètre : implémentation locale
du backend DiddiShop, routes métier, routes internes et webhooks.

Ce document décrit les garanties de l’implémentation actuelle. Il ne certifie
pas à lui seul le déploiement staging ni les contrats externes non authentifiés.
Les écarts et contrats à confirmer sont listés dans
[`open-questions.md`](open-questions.md).

## Références et surfaces

| Surface | Source locale | Usage |
| --- | --- | --- |
| OpenAPI runtime | `GET /openapi.json` | Schémas et opérations exposés par FastAPI |
| Santé | `GET /health` | Disponibilité du processus |
| Readiness | `GET /ready` | Vérification PostgreSQL et Redis |
| Routes publiques métier | `app_base/modules/*/router.py` | Acheteur, vendeur et commandes |
| Routes internes | `app_base/modules/*/presentation/router.py` | Support, Rewards, Comms et Observe |
| Webhooks | `POST /internal/v1/webhooks/*` | Événements DiddiPay et DiddiSend |

## Connexion HTTP

En développement, l’acteur est fourni par le contexte local et vaut
`anonymous` par défaut. En staging et production, les routes qui dépendent d’un
acteur exigent `Authorization: Bearer <access_token>` ; le JWT est vérifié via
les clés JWKS de DiddiFreeID.

Les appels sortants utilisent un client S2S propre à chaque cible :

- `X-Client-ID` correspond au client de la cible appelée ;
- le token est obtenu avec `client_credentials` et l’audience de la cible ;
- `X-Request-ID`, `traceparent`, `X-Origin-Service: diddishop` et
  `Idempotency-Key` sont propagés lorsque l’opération le permet ;
- DiddiObserve utilise son credential OTLP dédié et n’utilise pas un scope S2S
  métier.

Un token DiddiPay ne doit jamais être réutilisé pour DiddiSend. Les secrets ne
sont jamais transmis aux clients mobiles ou web.

## Inventaire HTTP

Les routes suivantes sont la surface métier actuellement montée par
`app_base/main.py`.

| Méthode | Route | Responsabilité |
| --- | --- | --- |
| GET | `/health` | Santé du processus |
| GET | `/ready` | Santé PostgreSQL/Redis |
| POST | `/v1/shops` | Créer une boutique |
| GET | `/v1/shops/{shop_id}` | Lire une boutique |
| POST | `/v1/catalog/shops/{shop_id}/products` | Créer un produit |
| POST | `/v1/catalog/products/{product_id}/publish` | Publier un produit |
| GET | `/v1/catalog/products/{product_id}` | Lire un produit |
| GET | `/v1/cart` | Lire le panier |
| POST | `/v1/cart/lines` | Ajouter ou modifier une ligne |
| POST | `/v1/checkouts` | Créer un checkout idempotent |
| GET | `/v1/orders/{order_id}` | Lire une commande |
| POST | `/v1/orders/{order_id}/transitions` | Demander une transition contrôlée |
| POST | `/v1/orders/{order_id}/confirm` | Confirmer la commande côté vendeur |
| POST | `/v1/orders/{order_id}/ready` | Marquer la commande prête |
| POST | `/v1/deliveries/orders/{order_id}` | Demander l’expédition DiddiSend |
| GET | `/v1/deliveries/orders/{order_id}` | Lire la projection livraison |
| POST | `/v1/claims/orders/{order_id}/cancel` | Demander l’annulation |
| POST | `/v1/claims/orders/{order_id}` | Ouvrir une réclamation |
| POST | `/v1/claims/{claim_id}/decision` | Décider une réclamation |
| GET | `/v1/campaigns/active` | Lire la projection des campagnes |
| GET | `/v1/admin/shop/capabilities` | Capacités backoffice exposées |
| GET | `/v1/admin/shop/orders/{order_id}` | Lire une commande pour opérateur |
| POST | `/v1/admin/shop/claims/{claim_id}/decision` | Décision opérateur idempotente |
| GET | `/internal/v1/support/orders/{order_id}/context` | Contexte support |
| GET | `/internal/v1/support/orders/{order_id}/context/live` | Contexte support enrichi |
| POST | `/internal/v1/support/orders/{order_id}/cases` | Créer un cas support |
| GET | `/internal/v1/comms/health` | Santé de l’adaptateur Comms |
| GET | `/internal/v1/rewards/health` | Santé de l’adaptateur Rewards |
| GET | `/internal/v1/observability/health` | Santé de l’observabilité locale |
| POST | `/internal/v1/webhooks/diddipay` | Événement DiddiPay signé |
| POST | `/internal/v1/webhooks/diddisend` | Événement DiddiSend signé |

Les schémas exacts sont ceux de `/openapi.json` du build exécuté. Une route
interne n’est pas une route publique : elle exige le contrôle S2S ou réseau
prévu par l’environnement cible.

## Conventions

| Sujet | Convention |
| --- | --- |
| Transport | HTTPS en environnement non local ; JSON pour les routes HTTP |
| Devise | `XOF` uniquement ; aucun taux de change ni conversion implicite |
| Montants | Entiers en unités mineures métier selon le contrat de chaque service ; ne jamais diviser silencieusement |
| Identifiants | Références opaques externes ; UUID lorsque le schéma le déclare |
| Temps | ISO 8601 UTC côté événements et intégrations |
| Corrélation | `request_id`, `correlation_id`, `traceparent` ; ces valeurs ne remplacent pas `event_id` |
| Rejeu | Relire l’état connu avant de créer une nouvelle opération après timeout |
| Erreurs | Piloter les actions par le code/statut, pas par le texte libre |

## Machine à états de commande

La commande possède deux axes séparés : `fulfillment_status` pour la
logistique et `payment_status` pour le paiement.

```text
PAYMENT_PENDING -> TO_CONFIRM -> TO_PREPARE -> READY_FOR_PICKUP
                                               |
                         +---------------------+-------------------+
                         v                                         v
                      PICKED_UP -> IN_TRANSIT -> DELIVERED      FAILED
                         |              |             |            |
                         +--------------+-------------+------------+
                                        v
                              RETURNED / DISPUTED -> CLOSED

PAYMENT_PENDING, TO_CONFIRM, TO_PREPARE, READY_FOR_PICKUP -> CANCELLED
```

`CANCELLED` et `CLOSED` sont terminaux. DiddiSend est la source de vérité du
suivi de livraison ; DiddiShop conserve uniquement la projection nécessaire à
la commande. `PaymentStatus` est séparé : un événement de livraison ne prouve
jamais le paiement et un remboursement ne change pas seul l’état logistique.

## Idempotence et événements

L’enveloppe interne stable est `EventEnvelope` :

```json
{
  "event_id": "uuid",
  "event_type": "order.status_changed",
  "event_version": 1,
  "occurred_at": "2026-11-25T12:00:00Z",
  "producer": "diddi-shop",
  "aggregate_type": "order",
  "aggregate_id": "order-id",
  "correlation_id": "correlation-id",
  "causation_id": "event-id-or-null",
  "payload": {}
}
```

Règles :

1. l’état et l’événement sortant sont écrits dans la même transaction métier ;
2. l’outbox est publiée au moins une fois ;
3. l’inbox déduplique par `consumer + event_id` ;
4. même clé et même payload = rejeu idempotent ; même clé et payload différent
   = conflit de contrat ;
5. une clé stable doit être conservée pour toute opération externe incertaine.

Clés minimales documentées :

| Opération | Clé |
| --- | --- |
| PaymentIntent | `shop:create-payment:{checkout_id}:1` |
| Refund | `shop:refund:{order_id}:{operation}` |
| Livraison | `shop:create-delivery:{order_id}:1` |
| Annulation livraison | `shop:cancel-delivery:{order_id}:{operation}` |
| Réservation Rewards | `shop:reward-reserve:{checkout_id}:1` |
| Conversation | `shop:conversation:{task_id}:1` |
| Cas support | `shop:claim-case:{claim_id}:1` |

## Webhooks

`POST /internal/v1/webhooks/diddipay` et `POST /internal/v1/webhooks/diddisend`
valident la signature configurée, consultent l’inbox, appliquent l’événement
une seule fois et renvoient `{"status":"duplicate"}` pour un événement déjà
traité. Une signature invalide ou un secret absent doit être traité comme un
échec d’authentification/configuration, jamais comme un événement métier.

Les noms d’événements attendus sont décrits dans les pages
[`diddipay.md`](../integrations/diddipay.md) et
[`diddisend.md`](../integrations/diddisend.md). Les catalogues fournisseurs
restent à confirmer lorsque le staging ne les publie pas.

## Limites explicites

- Les notifications SMS/WhatsApp déclenchées par événement ne sont pas
  définies par la route conversation DiddiComms.
- La séquestration marketplace et la release vendeur sont V2.
- DiddiShop ne dépend pas de DiddiMap et ne gère pas les coursiers.
- La conformité staging nécessite encore les credentials, scopes, secrets et
  essais authentifiés réels, sans transaction financière de recette.
