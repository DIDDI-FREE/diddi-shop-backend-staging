# Contrat API DiddiShop — HTTP et webhooks

Version documentaire : `draft.2026-11-26`. Périmètre : implémentation locale
du backend DiddiShop, routes métier, routes internes et webhooks.

Ce document décrit les garanties de l’implémentation actuelle. Il ne certifie
pas à lui seul le déploiement staging ni les contrats externes non authentifiés.
Les écarts et contrats à confirmer sont listés dans
[`open-questions.md`](open-questions.md).

L’audit exhaustif des routes, protocoles, valeurs et limites de couverture est
dans [`PROTOCOLS_AND_COVERAGE.md`](PROTOCOLS_AND_COVERAGE.md).

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

`X-Actor-ID` n’est pas un mécanisme d’authentification staging : il n’est pris
en compte qu’en environnement `development` pour les tests locaux. Le frontend
staging doit donc toujours envoyer le Bearer JWT DiddiFreeID.

Les appels sortants utilisent un client S2S propre à chaque cible :

- `X-Client-ID` correspond au client de la cible appelée ;
- le token est obtenu avec `client_credentials` et l’audience de la cible ;
- `X-Request-ID`, `traceparent`, `X-Origin-Service: diddishop` et
  `Idempotency-Key` sont propagés lorsque l’opération le permet ;
- DiddiObserve utilise son credential OTLP dédié et n’utilise pas un scope S2S
  métier.

Un token DiddiPay ne doit jamais être réutilisé pour DiddiSend. Les secrets ne
sont jamais transmis aux clients mobiles ou web.

## CORS frontend

L’API autorise les origines HTTP et HTTPS correspondant à un sous-domaine de
`diddifree.com` (`*.diddifree.com`) ainsi que `localhost` avec un port
optionnel. Les méthodes et headers nécessaires au frontend, notamment
`Authorization`, sont acceptés. Les credentials navigateur ne sont pas
activés : l’authentification frontend utilise un Bearer JWT et non un cookie.
Les autres origines ne reçoivent aucun header CORS.

## Inventaire HTTP

Les routes suivantes sont la surface métier actuellement montée par
`app_base/main.py`.

| Méthode | Route | Responsabilité |
| --- | --- | --- |
| GET | `/health` | Santé du processus |
| GET | `/ready` | Santé PostgreSQL/Redis |
| POST | `/v1/shops` | Créer une boutique |
| GET | `/v1/shops/mine` | Lister les boutiques du vendeur connecté |
| GET | `/v1/shops/{shop_id}` | Lire une boutique publique |
| POST | `/v1/catalog/shops/{shop_id}/products` | Créer un produit |
| GET | `/v1/catalog/products` | Catalogue publié, recherche et catégorie |
| GET | `/v1/catalog/categories` | Codes de catégories recommandés pour l’affichage |
| GET | `/v1/catalog/shops/{shop_id}/products` | Produits publiés d’une boutique |
| GET | `/v1/catalog/my-products` | Produits du vendeur connecté |
| POST | `/v1/catalog/products/{product_id}/publish` | Publier un produit |
| PATCH | `/v1/catalog/products/{product_id}` | Modifier prix, stock ou contenu vendeur |
| POST | `/v1/catalog/products/{product_id}/photos/upload-session` | Créer une session d’upload DiddiFiles |
| POST | `/v1/catalog/products/{product_id}/photos` | Attacher une photo DiddiFiles confirmée |
| GET | `/v1/catalog/products/{product_id}/photos` | Obtenir les URLs des photos produit |
| GET | `/v1/catalog/products/{product_id}` | Lire un produit |
| GET | `/v1/cart` | Lire le panier |
| POST | `/v1/cart/lines` | Ajouter ou modifier une ligne |
| DELETE | `/v1/cart/lines/{product_id}` | Retirer complètement une ligne |
| POST | `/v1/checkouts` | Créer un checkout idempotent |
| GET | `/v1/orders` | Lister les commandes de l’acheteur connecté |
| GET | `/v1/orders/seller/to-confirm` | Lister les commandes vendeur à confirmer |
| GET | `/v1/orders/{order_id}` | Lire une commande |
| POST | `/v1/orders/{order_id}/transitions` | Demander une transition contrôlée |
| POST | `/v1/orders/{order_id}/confirm` | Confirmer la commande côté vendeur |
| POST | `/v1/orders/{order_id}/ready` | Marquer la commande prête |
| POST | `/v1/deliveries/orders/{order_id}` | Reprise contrôlée de l’expédition DiddiSend |
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
| Erreurs | Réponse JSON `{error, message, details?}` ; piloter par `error` et HTTP status |

## Réponses frontend V1

Les listes utilisent toujours une enveloppe `{ "items": [...] }`. Les montants
sont des entiers XOF et les statuts sont des chaînes stables.

### Produit

```json
{
  "id": "product-id",
  "shop_id": "shop-id",
  "title": "Article",
  "description": "Description",
  "price_minor": 2500,
  "currency": "XOF",
  "stock": 4,
  "category": "books",
  "status": "published",
  "photo_file_ids": ["file-id"],
  "photo_urls": []
}
```

Les valeurs de `status` sont `draft`, `published`, `paused` et `retired`.
`stock=0` ne crée pas un statut supplémentaire : l’article reste dans son état
de publication, mais ne peut pas être ajouté au panier si le stock est
insuffisant. Les listes publiques ne renvoient que les produits `published`.

### Boutique

`GET /v1/shops/{shop_id}` renvoie une boutique publique sous cette forme :

```json
{
  "id": "shop-id",
  "owner_id": "seller-id",
  "name": "Ma boutique",
  "pickup_address": "Adresse de retrait",
  "pickup_latitude": 3.8480,
  "pickup_longitude": 11.5021,
  "status": "active"
}
```

`GET /v1/shops/mine` renvoie `{ "items": [<boutique>] }`. Les statuts de
boutique sont `active` et `suspended`.

### Catégories

`GET /v1/catalog/categories` renvoie les codes recommandés et leurs libellés
français :

```json
{
  "items": [
    {"code": "fashion", "name": "Mode"},
    {"code": "beauty", "name": "Beauté"},
    {"code": "home", "name": "Maison"},
    {"code": "electronics", "name": "Électronique"},
    {"code": "food", "name": "Alimentation"},
    {"code": "books", "name": "Livres"},
    {"code": "sports", "name": "Sports"},
    {"code": "services", "name": "Services"},
    {"code": "other", "name": "Autre"}
  ]
}
```

La valeur envoyée dans `category` reste compatible avec les données existantes
et n’est pas encore bloquée par cette liste. Le frontend doit utiliser ces
codes pour les nouvelles créations.

### Panier et commande

Un panier contient `id`, `customer_id`, `currency`, `lines` et `line_count`.
Chaque ligne contient `product_id`, `shop_id` et `quantity`. Une suppression
se fait par `DELETE /v1/cart/lines/{product_id}` ; la quantité d’une ligne
conservée reste toujours supérieure ou égale à 1.

Une commande contient `id`, `shop_id`, `checkout_id`, `total_minor`, `currency`,
`fulfillment_status`, `payment_status`, `delivery_id`, `version`,
`payment_intent_id` et `items`.

### Photos produit et DiddiFiles

`POST /v1/catalog/products/{product_id}/photos/upload-session` renvoie le
contrat DiddiFiles suivant :

```json
{
  "file_id": "file-id",
  "status": "pending",
  "upload": {
    "method": "PUT",
    "url": "https://s3.example/upload",
    "expires_in_seconds": 900,
    "headers": {"Content-Type": "image/jpeg"}
  }
}
```

Le frontend envoie le binaire avec `PUT` vers `upload.url` et les headers
retournés. Il ne possède pas de credential S2S DiddiFiles. Ensuite, il appelle
`POST /v1/catalog/products/{product_id}/photos` avec `{ "file_id": "..." }`.
DiddiShop appelle alors `POST /v1/files/{file_id}/confirm` côté DiddiFiles,
vérifie le purpose `diddishop_product_image`, puis attache le fichier au
produit. La confirmation n’est donc pas faite directement par l’application
frontend.

`GET /v1/catalog/products/{product_id}/photos` renvoie :

```json
{"items": [{"file_id": "file-id", "url": "https://files.example/photo"}]}
```

Les réponses produit des listes (`/products`, `/shops/{shop_id}/products` et
`/my-products`) remplissent également `photo_urls` lorsque DiddiFiles fournit
une URL publique ou signée.

### Schémas OpenAPI

`GET /openapi.json` décrit maintenant les schémas de réponse utilisés par le
frontend : `ShopResponse`, `ShopListResponse`, `CategoryListResponse`,
`ProductResponse`, `ProductListResponse`, `ProductPhotoListResponse`,
`CartResponse`, `OrderResponse`, `OrderListResponse`, `CheckoutResponse` et
`UploadSessionResponse`. Le frontend peut donc générer ses types à partir de
l’OpenAPI runtime au lieu de déduire les champs des exemples.

### Checkout et paiement

`POST /v1/checkouts` renvoie le checkout et le résultat normalisé de DiddiPay :

```json
{
  "id": "checkout-id",
  "customer_id": "buyer-id",
  "total_minor": 3500,
  "currency": "XOF",
  "status": "payment_pending",
  "order_ids": ["order-id"],
  "payment": {
    "payment_intent_id": "payment-id",
    "amount_minor": 3500,
    "currency": "XOF",
    "status": "pending"
  }
}
```

Les champs optionnels fournis par DiddiPay (`payment_url`, `checkout_url` ou
`client_secret`) sont relayés lorsqu’ils existent. Les données carte, tokens
et secrets ne sont jamais relayés.

### Erreurs

Les codes V1 sont `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`,
`INVALID_TRANSITION`, `VALIDATION_ERROR`, `NOT_CONFIGURED` et `HTTP_ERROR`.
Exemple :

```json
{
  "error": "NOT_FOUND",
  "message": "product not found"
}
```

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

### Déclenchement de l’expédition

Le vendeur signale la fin de préparation avec
`POST /v1/orders/{order_id}/ready`. DiddiShop effectue alors, dans ce use case,
la transition `TO_PREPARE -> READY_FOR_PICKUP`, appelle DiddiSend avec la clé
`shop:create-delivery:{order_id}:1` et enregistre `delivery_id`. Le frontend
vendeur ne doit pas appeler directement la route de création DiddiSend.

La commande `ready` est rejouable : si l’état est déjà `READY_FOR_PICKUP` et
qu’une projection existe, DiddiShop renvoie la projection sans créer une
seconde livraison. La route `POST /v1/deliveries/orders/{order_id}` est une
opération de reprise réservée à l’exploitation.

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
