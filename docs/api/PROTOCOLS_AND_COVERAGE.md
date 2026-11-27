# Protocoles et couverture API

**Audit :** 2026-11-26  
**Source d’exécution :** `GET /openapi.json` du build DiddiShop

Cette page complète le contrat HTTP principal. Elle distingue les routes
réellement montées, les protocoles utilisés et les réponses qui disposent déjà
d’un schéma OpenAPI explicite.

La description détaillée de chaque route, de ses paramètres, contraintes,
réponses et limites est dans
[`ROUTE_REFERENCE.md`](ROUTE_REFERENCE.md).

## Protocoles utilisés

| Protocole | Usage | Statut |
| --- | --- | --- |
| REST/HTTP JSON | API acheteur, vendeur, backoffice et modules internes | actif |
| HTTP HTML | retour navigateur public `/payments/return`, sans confirmation financière | actif |
| HTTP webhooks JSON | événements entrants DiddiPay et DiddiSend | actif |
| HTTP S2S Bearer | appels sortants vers DiddiPay, DiddiSend, DiddiFiles, Rewards, Support et Comms | actif |
| OAuth2 client credentials | obtention des tokens S2S par service cible | actif en configuration non-développement |
| OTLP HTTP/protobuf | logs et traces DiddiObserve | actif |
| PostgreSQL | persistance métier, outbox/inbox et idempotence | interne |
| Redis | cache/coordination d’exécution | interne |
| WebSocket | temps réel navigateur | **non implémenté** |

DiddiShop ne publie aucune route WebSocket et ne promet donc ni `ws://`, ni
`wss://`, ni abonnement temps réel. Le frontend utilise les lectures REST et les
changements de livraison arrivent par webhooks DiddiSend, projetés localement.

## Authentification et headers

### Frontend

- développement : `X-Actor-ID` peut sélectionner l’acteur local ; à défaut,
  l’acteur est `anonymous` ;
- staging/production : `Authorization: Bearer <DiddiFreeID JWT>` obligatoire
  pour les routes dépendant d’un acteur ;
- CORS : sous-domaines `*.diddifree.com` et `localhost` avec port optionnel ;
- credentials navigateur : désactivés ;
- `X-Actor-ID` n’est pas accepté comme authentification staging.

### Appels S2S

- un client et un secret par service cible ;
- token obtenu avec `client_credentials` ;
- `X-Client-ID`, `X-Origin-Service: diddishop`, `X-User-ID` ;
- `X-Request-ID` et `traceparent` pour la corrélation ;
- `Idempotency-Key` pour les commandes rejouables ;
- aucun secret S2S transmis au frontend.

### Webhooks fournisseurs

- DiddiPay : `X-DiddiPay-Signature` contient un HMAC-SHA256 du corps JSON exact
  envoyé par DiddiPay ; aucun `X-Webhook-Timestamp` n'entre dans le calcul ;
- le secret entrant est `DIDDI_SHOP_DIDDIPAY_WEBHOOK_SECRET`, configuré dans
  `PAYMENT_CALLBACK_TARGETS` côté DiddiPay ; il est différent du secret S2S
  utilisé par DiddiShop pour obtenir un token et appeler DiddiPay ;
- enveloppe DiddiPay : `{id, type, occurred_at, data}` ; l'identification du
  checkout repose sur `data.checkout_id` ou
  `data.business_reference=diddishop:checkout:{checkout_id}` ;
- DiddiPay est dédupliqué par `id` dans l'inbox `diddishop-diddipay` ; un
  callback déjà traité répond `{"status":"duplicate"}` ;
- aucune donnée de callback n'est acceptée sans signature valide en staging.

### Observabilité

DiddiObserve utilise OTLP HTTP/protobuf, `Content-Type: application/x-protobuf`
et un credential Basic dédié. Il n’utilise pas les scopes métier S2S et ne reçoit
jamais de JSON applicatif brut.

## Inventaire exhaustif des routes métier

Les routes ci-dessous sont les chemins métier présents dans l’OpenAPI du
build audité. Les routes `/openapi.json`, `/docs` et `/redoc` sont des routes
techniques FastAPI et le portail MkDocs est servi séparément.

### Santé et identité métier

| Méthode | Route | Réponse OpenAPI |
| --- | --- | --- |
| GET | `/health` | `HealthResponse` |
| GET | `/ready` | `ReadinessResponse` |
| POST | `/v1/shops` | `ShopResponse` |
| GET | `/v1/shops/mine` | `ShopListResponse` |
| GET | `/v1/shops/{shop_id}` | `ShopResponse` |

### Catalogue, médias et panier

| Méthode | Route | Réponse OpenAPI |
| --- | --- | --- |
| GET | `/v1/catalog/categories` | `CategoryListResponse` |
| POST | `/v1/catalog/shops/{shop_id}/products` | `ProductResponse` |
| GET | `/v1/catalog/products` | `ProductListResponse` |
| GET | `/v1/catalog/shops/{shop_id}/products` | `ProductListResponse` |
| GET | `/v1/catalog/my-products` | `ProductListResponse` |
| GET | `/v1/catalog/products/{product_id}` | `ProductResponse` |
| PATCH | `/v1/catalog/products/{product_id}` | `ProductResponse` |
| POST | `/v1/catalog/products/{product_id}/publish` | `ProductResponse` |
| POST | `/v1/catalog/products/{product_id}/pause` | `ProductResponse` |
| POST | `/v1/catalog/products/{product_id}/retire` | `ProductResponse` |
| POST | `/v1/catalog/products/{product_id}/photos/upload-session` | `UploadSessionResponse` |
| POST | `/v1/catalog/products/{product_id}/photos` | `ProductResponse` |
| GET | `/v1/catalog/products/{product_id}/photos` | `ProductPhotoListResponse` |
| GET | `/v1/cart` | `CartResponse` |
| POST | `/v1/cart/lines` | `CartResponse` |
| PATCH | `/v1/cart/lines/{product_id}` | `CartResponse` |
| DELETE | `/v1/cart/lines/{product_id}` | `CartResponse` |

### Checkout, commandes et livraison

| Méthode | Route | Réponse OpenAPI |
| --- | --- | --- |
| POST | `/v1/checkouts` | `CheckoutResponse` |
| POST | `/v1/checkouts/quote` | `CheckoutQuoteResponse` |
| GET | `/v1/checkouts/{checkout_id}` | `CheckoutResponse` |
| POST | `/v1/checkouts/{checkout_id}/retry` | `CheckoutResponse` |
| GET | `/payments/return` | HTML neutre, aucun état de paiement |
| GET | `/v1/orders` | `OrderListResponse` |
| GET | `/v1/orders/seller/to-confirm` | `OrderListResponse` |
| GET | `/v1/orders/{order_id}` | `OrderResponse` |
| POST | `/v1/orders/{order_id}/transitions` | `OrderResponse` |
| POST | `/v1/orders/{order_id}/confirm` | `OrderResponse` |
| POST | `/v1/orders/{order_id}/ready` | `OrderResponse` |
| POST | `/v1/deliveries/orders/{order_id}` | `DeliveryResponse` |
| GET | `/v1/deliveries/orders/{order_id}` | `DeliveryResponse` |

Le frontend vendeur appelle `POST /v1/orders/{order_id}/ready`. DiddiShop
déclenche ensuite DiddiSend. Le frontend ne doit pas appeler directement la
route de création livraison.

### Annulations, claims et campagnes

| Méthode | Route | Réponse OpenAPI |
| --- | --- | --- |
| POST | `/v1/claims/orders/{order_id}/cancel` | `OrderResponse` |
| POST | `/v1/claims/orders/{order_id}` | `ClaimResponse` |
| GET | `/v1/claims/orders/{order_id}` | `ClaimResponse` |
| POST | `/v1/claims/orders/{order_id}/evidence/upload-session` | `UploadSessionResponse` |
| POST | `/v1/claims/{claim_id}/decision` | `ClaimResponse` |
| GET | `/v1/campaigns/active` | `CampaignListResponse` |

### Backoffice et modules internes

| Méthode | Route | Réponse OpenAPI |
| --- | --- | --- |
| GET | `/v1/admin/shop/capabilities` | `AdminCapabilitiesResponse` |
| GET | `/v1/admin/shop/orders/{order_id}` | `AdminOrderResponse` |
| POST | `/v1/admin/shop/claims/{claim_id}/decision` | `ClaimResponse` |
| GET | `/internal/v1/comms/health` | `CommsHealthResponse` |
| GET | `/internal/v1/observability/health` | `ObservabilityHealthResponse` |
| GET | `/internal/v1/rewards/health` | `RewardsHealthResponse` |
| GET | `/internal/v1/support/orders/{order_id}/context` | `SupportContextResponse` |
| GET | `/internal/v1/support/orders/{order_id}/context/live` | `SupportContextResponse` |
| POST | `/internal/v1/support/orders/{order_id}/cases` | `SupportCaseResponse` |
| POST | `/internal/v1/webhooks/diddipay` | `WebhookResponse` |
| POST | `/internal/v1/webhooks/diddisend` | `WebhookResponse` |

## Valeurs et états

### Catalogue

- produit : `draft`, `published`, `paused`, `retired` ;
- boutique : `active`, `suspended` ;
- devise : `XOF` uniquement ;
- catégories recommandées : `fashion`, `beauty`, `home`, `electronics`,
  `food`, `books`, `sports`, `services`, `other` ;
- `stock=0` n’est pas un état supplémentaire ;
- maximum de photos : `8` ; formats acceptés : `image/jpeg`, `image/png`,
  `image/webp` ; taille d’upload maximale : `10 MiB` ;

### Checkout et commande

- checkout : `payment_pending`, `payment_succeeded`, `payment_failed` ;
- `expires_at` est renvoyé en ISO 8601 UTC (`...Z`) lorsqu’il est fourni par
  DiddiPay. DiddiPay reste la source de vérité : DiddiShop ne crée pas
  localement un état `payment_expired` et attend un webhook pour conclure.
- fulfillment : `PAYMENT_PENDING`, `TO_CONFIRM`, `TO_PREPARE`,
  `READY_FOR_PICKUP`, `PICKED_UP`, `IN_TRANSIT`, `DELIVERED`, `RETURNED`,
  `CANCELLED`, `FAILED`, `DISPUTED`, `CLOSED` ;
- paiement : `PENDING`, `HELD`, `REFUND_PENDING`, `REFUNDED`,
  `PARTIALLY_REFUNDED`, `RELEASE_BLOCKED`, `RELEASE_PENDING`, `RELEASED` ;
- réclamation : `buyer`, `seller`, `partial`, `rejected`.

### Livraison

La projection locale utilise : `requested`, `assigned`, `picked_up`,
`in_transit`, `delivered`, `failed`, `returned`. DiddiSend reste propriétaire
du coursier, du code de remise, de la position et du suivi opérationnel.
`courier` est normalisé avec `id`, `name`, `phone_masked`, `avatar_url` et
`vehicle_type` vaut `motorbike`, `cargo_bike`, `tricycle`, `car`, `van` ou
`truck` ; les alias entrants `moto` et `motorcycle` deviennent `motorbike`.
`position` utilise `latitude`, `longitude` et `updated_at` ; `updated_at` reste
facultatif si DiddiSend ne le fournit pas dans l’événement.

## Contrats encore dépendants d’un service externe

Les contrats HTTP DiddiShop ci-dessus sont typés et vérifiés localement. Restent
à valider sur staging, sans les inventer côté frontend :

1. les champs additionnels réellement envoyés par DiddiSend dans `courier`,
   `position`, `dropoff_code` et `tracking` ;
2. les URLs et champs optionnels effectivement fournis par DiddiPay pour le
   parcours mobile money ;
3. les credentials S2S et les scopes dédiés par cible ;
4. la disponibilité réelle de PostgreSQL, Redis et des endpoints OTLP.

Ces points sont des vérifications d’intégration/environnement, pas des trous de
schéma dans l’API DiddiShop.
