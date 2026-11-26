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

### Observabilité

DiddiObserve utilise OTLP HTTP/protobuf, `Content-Type: application/x-protobuf`
et un credential Basic dédié. Il n’utilise pas les scopes métier S2S et ne reçoit
jamais de JSON applicatif brut.

## Inventaire exhaustif des routes métier

Les routes ci-dessous sont les 39 chemins métier présents dans l’OpenAPI du
build audité. Les routes `/openapi.json`, `/docs` et `/redoc` sont des routes
techniques FastAPI et le portail MkDocs est servi séparément.

### Santé et identité métier

| Méthode | Route | Réponse OpenAPI |
| --- | --- | --- |
| GET | `/health` | à typer explicitement |
| GET | `/ready` | à typer explicitement |
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
| POST | `/v1/catalog/products/{product_id}/photos/upload-session` | `UploadSessionResponse` |
| POST | `/v1/catalog/products/{product_id}/photos` | `ProductResponse` |
| GET | `/v1/catalog/products/{product_id}/photos` | `ProductPhotoListResponse` |
| GET | `/v1/cart` | `CartResponse` |
| POST | `/v1/cart/lines` | `CartResponse` |
| DELETE | `/v1/cart/lines/{product_id}` | `CartResponse` |

### Checkout, commandes et livraison

| Méthode | Route | Réponse OpenAPI |
| --- | --- | --- |
| POST | `/v1/checkouts` | `CheckoutResponse` |
| GET | `/v1/orders` | `OrderListResponse` |
| GET | `/v1/orders/seller/to-confirm` | `OrderListResponse` |
| GET | `/v1/orders/{order_id}` | `OrderResponse` |
| POST | `/v1/orders/{order_id}/transitions` | `OrderResponse` |
| POST | `/v1/orders/{order_id}/confirm` | `OrderResponse` |
| POST | `/v1/orders/{order_id}/ready` | `OrderResponse` |
| POST | `/v1/deliveries/orders/{order_id}` | **à typer** |
| GET | `/v1/deliveries/orders/{order_id}` | **à typer** |

Le frontend vendeur appelle `POST /v1/orders/{order_id}/ready`. DiddiShop
déclenche ensuite DiddiSend. Le frontend ne doit pas appeler directement la
route de création livraison.

### Annulations, claims et campagnes

| Méthode | Route | Réponse OpenAPI |
| --- | --- | --- |
| POST | `/v1/claims/orders/{order_id}/cancel` | **à typer** |
| POST | `/v1/claims/orders/{order_id}` | **à typer** |
| POST | `/v1/claims/{claim_id}/decision` | **à typer** |
| GET | `/v1/campaigns/active` | **à typer** |

### Backoffice et modules internes

| Méthode | Route | Réponse OpenAPI |
| --- | --- | --- |
| GET | `/v1/admin/shop/capabilities` | **à typer** |
| GET | `/v1/admin/shop/orders/{order_id}` | **à typer** |
| POST | `/v1/admin/shop/claims/{claim_id}/decision` | **à typer** |
| GET | `/internal/v1/comms/health` | **à typer** |
| GET | `/internal/v1/observability/health` | **à typer** |
| GET | `/internal/v1/rewards/health` | **à typer** |
| GET | `/internal/v1/support/orders/{order_id}/context` | **à typer** |
| GET | `/internal/v1/support/orders/{order_id}/context/live` | **à typer** |
| POST | `/internal/v1/support/orders/{order_id}/cases` | **à typer** |
| POST | `/internal/v1/webhooks/diddipay` | **à typer** |
| POST | `/internal/v1/webhooks/diddisend` | **à typer** |

## Valeurs et états

### Catalogue

- produit : `draft`, `published`, `paused`, `retired` ;
- boutique : `active`, `suspended` ;
- devise : `XOF` uniquement ;
- catégories recommandées : `fashion`, `beauty`, `home`, `electronics`,
  `food`, `books`, `sports`, `services`, `other` ;
- `stock=0` n’est pas un état supplémentaire ;
- les formats photo et le nombre maximal de photos restent à formaliser.

### Checkout et commande

- checkout : `payment_pending`, `payment_succeeded`, `payment_failed` ;
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

## Ce qui reste à compléter

La couverture des chemins ne signifie pas que tous les contrats sont terminés.
Les éléments suivants doivent encore recevoir des modèles de réponse explicites
et être ajoutés à l’OpenAPI :

1. projection livraison et détails de suivi ;
2. réponse d’annulation et erreurs d’éligibilité ;
3. lignes de commande, échéance vendeur et `created_at` ;
4. devis checkout et ventilation des montants ;
5. statut et relance du paiement ;
6. réponses admin, support, Rewards, Comms et webhooks ;
7. règles de validation des adresses, téléphone et photos.

Cette liste est volontairement visible : MkDocs ne doit pas présenter une route
comme contractuellement complète tant que son schéma de réponse réel n’est pas
figé.
