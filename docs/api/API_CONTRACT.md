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
| POST | `/v1/catalog/products/{product_id}/pause` | Mettre en pause un produit |
| POST | `/v1/catalog/products/{product_id}/retire` | Retirer définitivement un produit |
| PATCH | `/v1/catalog/products/{product_id}` | Modifier prix, stock ou contenu vendeur |
| POST | `/v1/catalog/products/{product_id}/photos/upload-session` | Créer une session d’upload DiddiFiles |
| POST | `/v1/catalog/products/{product_id}/photos` | Attacher une photo DiddiFiles confirmée |
| GET | `/v1/catalog/products/{product_id}/photos` | Obtenir les URLs des photos produit |
| GET | `/v1/catalog/products/{product_id}` | Lire un produit |
| GET | `/v1/cart` | Lire le panier |
| POST | `/v1/cart/lines` | Ajouter ou modifier une ligne |
| PATCH | `/v1/cart/lines/{product_id}` | Fixer la quantité exacte d’une ligne |
| DELETE | `/v1/cart/lines/{product_id}` | Retirer complètement une ligne |
| POST | `/v1/checkouts` | Créer un checkout idempotent |
| POST | `/v1/checkouts/quote` | Calculer le devis avant paiement |
| GET | `/v1/checkouts/{checkout_id}` | Lire l’état d’un checkout |
| POST | `/v1/checkouts/{checkout_id}/retry` | Reprendre un paiement échoué |
| GET | `/payments/return` | Retour navigateur HTML public, sans confirmation du paiement |
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
| GET | `/v1/claims/orders/{order_id}` | Relire la réclamation d’une commande |
| POST | `/v1/claims/orders/{order_id}/evidence/upload-session` | Préparer une preuve photo |
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

Un panier contient `id`, `customer_id`, `currency`, `lines`, `line_count`,
`subtotal_minor` et `shop_subtotals`. Chaque ligne contient `product_id`,
`shop_id`, `quantity`, `title`, `unit_price_minor` et `line_total_minor`. Une
suppression se fait par `DELETE /v1/cart/lines/{product_id}` ; la quantité
d’une ligne conservée reste toujours supérieure ou égale à 1.

Une commande contient `id`, `shop_id`, `checkout_id`, `total_minor`, `currency`,
`fulfillment_status`, `payment_status`, `delivery_id`, `version`,
`payment_intent_id`, `items`, `subtotal_minor`, `delivery_fee_minor`,
`discount_minor`, `created_at`, `seller_confirmation_deadline`,
`delivered_at`, `status_history`, `recipient_name` et `dropoff_address`. Chaque ligne de `items` expose
`product_id`, `title`, `unit_price_minor`, `quantity` et `line_total_minor`.

`GET /v1/orders` accepte `limit` (1–100, défaut 20) et un `cursor` opaque. La
réponse contient `items` et `next_cursor`.

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
`CartResponse`, `OrderResponse`, `OrderListResponse`, `CheckoutResponse`,
`CheckoutQuoteResponse`, `DeliveryResponse`, `ClaimResponse`, les réponses
admin/support et `UploadSessionResponse`. Le frontend peut donc générer ses
types à partir de l’OpenAPI runtime au lieu de déduire les champs des exemples.

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

Avant le paiement, `POST /v1/checkouts/quote` renvoie `subtotal_minor`,
`delivery_fee_minor`, `discount_minor`, `total_minor` et une ventilation
`shop_breakdowns` par boutique. Après création, `GET /v1/checkouts/{id}` lit le
statut `payment_pending`, `payment_succeeded` ou `payment_failed`. Une reprise
se fait avec `POST /v1/checkouts/{id}/retry`, uniquement après
`payment_failed`, avec une nouvelle clé d’idempotence. `payment_attempt` expose
le numéro de tentative sans exposer de secret DiddiPay. Le moyen de paiement
V1 est `wave`, `mtn_momo` ou `orange_money` ; `return_url` est facultative mais
transmise sous le nom `callback_url` DiddiPay. `return_target` (1–64 caractères)
est une alternative exclusive préconfigurée chez Pay. Sans ces options, Shop
utilise sa configuration : par défaut sa page publique `/payments/return`.
Les URLs explicites doivent être HTTPS sur `diddifree.com` ou un sous-domaine,
sans credentials, fragment ni traversée de chemin (2048 caractères maximum).
Le retry accepte ces mêmes options dans un corps facultatif pour réparer un
ancien checkout ; la clé d’idempotence couvre aussi ce corps.

Le retry peut également contenir `payment_method` avec l’une des valeurs
`wave`, `mtn_momo` ou `orange_money`. Le téléphone complet du payeur est
retourné dans `payment.customer_phone`, avec le moyen utilisé dans
`payment.payment_method`.

`payment.next_action` expose `type`, `url?`, `instructions?`, `expires_at?`.
Pour `redirect`, ouvrir `payment.payment_url`, égal à `next_action.url`.
`requires_action` n'est pas un paiement réussi : le checkout reste pending.
`GET /payments/return` est une page HTML neutre ; relire le checkout authentifié
après retour dans l'app. Le navigateur ne confirme jamais le paiement.

Le téléphone `recipient_phone` validé en E.164 devient `customer_phone` dans
le JSON envoyé à DiddiPay, y compris lors du retry. Sans téléphone valide dans
les données persistées, le retry retourne `422 PAYMENT_PHONE_REQUIRED` sans
appel fournisseur et sans incrémenter `payment_attempt`.

Création et retry renvoient le header `Idempotency-Replayed` (`true`/`false`),
accessible via CORS : `true` signifie que la réponse mémorisée est rejouée,
sans nouvelle tentative. Une erreur historique peut donc réapparaître avec
la même clé. Après un échec confirmé, une nouvelle tentative nécessite une
clé jamais utilisée ; après une réponse perdue, conserver la clé existante.

### Erreurs

Les codes V1 sont `UNAUTHENTICATED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`,
`INVALID_TRANSITION`, `ORDER_NOT_CANCELLABLE`, `DELIVERY_ALREADY_PICKED_UP`,
`VALIDATION_ERROR`, `PAYMENT_PHONE_REQUIRED`, `PAYMENT_RETURN_REQUIRED`,
`PAYMENT_RETURN_INVALID`, `NOT_CONFIGURED` et `HTTP_ERROR`.
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

DiddiPay signe le corps JSON exact avec HMAC-SHA256 et transmet la signature
dans `X-DiddiPay-Signature`. Son enveloppe est `{id, type, occurred_at, data}` ;
le secret entrant `DIDDI_SHOP_DIDDIPAY_WEBHOOK_SECRET` est distinct du
credential S2S utilisé par DiddiShop pour appeler DiddiPay. La référence métier
`diddishop:checkout:{checkout_id}` permet de rattacher le callback au checkout.
DiddiSend utilise le même principe HMAC sur son corps exact, mais avec
`X-DiddiSend-Signature` et le préfixe `sha256=` ; son enveloppe porte
`event_id`, `event_type`, `delivery_id` et `order_reference`.

Les noms d’événements attendus sont décrits dans les pages
[`diddipay.md`](../integrations/diddipay.md) et
[`diddisend.md`](../integrations/diddisend.md). Les catalogues fournisseurs
restent à confirmer lorsque le staging ne les publie pas.

### Réclamations

Une réclamation utilise un `reason_code` contrôlé : `not_as_described`,
`damaged`, `incomplete`, `missing_item` ou `other`, avec un commentaire texte
facultatif. Jusqu’à trois preuves photo peuvent être uploadées avec le purpose
DiddiFiles `diddishop_claim_evidence`. `claim_deadline` est calculée à
`delivered_at + 72 heures`.

Les codes d’erreur sont `CLAIM_WINDOW_EXPIRED` et `CLAIM_ALREADY_OPEN`. Le
remboursement est affiché par un statut, un moyen et une référence masquée ;
aucun numéro de téléphone complet n’est envoyé au frontend.

## Limites explicites

- Les notifications SMS/WhatsApp déclenchées par événement ne sont pas
  définies par la route conversation DiddiComms.
- La séquestration marketplace et la release vendeur sont V2.
- DiddiShop ne dépend pas de DiddiMap et ne gère pas les coursiers.
- La conformité staging nécessite encore les credentials, scopes, secrets et
  essais authentifiés réels, sans transaction financière de recette.
