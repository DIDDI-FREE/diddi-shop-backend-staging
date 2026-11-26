# Référence détaillée des routes

**Révision :** 2026-11-26  
**Source :** routes FastAPI, modèles Pydantic et services DiddiShop du build

Cette page est la référence opérationnelle route par route. Les contraintes
marquées **implémentées** sont vérifiées par le code. Les contraintes marquées
**à corriger** sont documentées pour éviter que le frontend les déduise ou les
considère disponibles par erreur.

## Conventions communes

### Authentification

| Marqueur | Signification |
| --- | --- |
| `JWT` | `Authorization: Bearer <DiddiFreeID JWT>` en staging/production ; acteur local en développement |
| `JWT vendeur` | JWT dont le sujet possède la boutique ou le produit concerné |
| `S2S/interne` | appel réservé au réseau ou au credential de service prévu pour l’environnement |
| `Webhook` | signature `X-Webhook-Signature` et `X-Webhook-Timestamp` obligatoires |
| `Aucun` | aucune dépendance d’acteur dans le code actuel ; à ne pas interpréter comme public sans protection réseau |

En développement, `X-Actor-ID` est accepté et l’acteur par défaut est
`anonymous`. En staging/production, `X-Actor-ID` ne remplace jamais le Bearer.

### Erreurs

Les erreurs métier utilisent l’enveloppe :

```json
{
  "error": "CONFLICT",
  "message": "human readable message"
}
```

Codes : `UNAUTHENTICATED` (401), `FORBIDDEN` (403), `NOT_FOUND` (404),
`CONFLICT` (409), `INVALID_TRANSITION` (409), `VALIDATION_ERROR` (422),
`NOT_CONFIGURED` (503), `RATE_LIMITED` (429) et `HTTP_ERROR` pour les autres
erreurs HTTP. Les réponses de validation peuvent aussi contenir `details`.

### Montants

Tous les montants sont des entiers et portent `currency: "XOF"`. Dans le code
actuel, `price_minor=2500` est transmis comme **2500 XOF** ; il ne faut pas le
convertir en devise ou le diviser côté frontend. Le nom `minor` est historique
et doit être clarifié dans un futur contrat sans changer silencieusement les
valeurs existantes.

## Santé

### `GET /health`

- Auth : aucune.
- Réponse 200 : `{"service":"diddishop","status":"ok"}`.
- Usage : liveness uniquement ; ne garantit ni PostgreSQL ni Redis.

### `GET /ready`

- Auth : aucune.
- Réponse 200 :

```json
{
  "service": "diddishop",
  "status": "ready",
  "dependencies": {"postgres": "ok", "redis": "ok"}
}
```

- `status` vaut `ready` si les deux dépendances répondent `ok`, sinon
  `not_ready`.

## Boutiques

### `POST /v1/shops`

- Auth : `JWT`.
- Corps obligatoire :

| Champ | Type | Contraintes |
| --- | --- | --- |
| `name` | string | 1 à 160 caractères |
| `pickup_address` | string | 1 à 500 caractères |
| `pickup_latitude` | number | obligatoire ; plage géographique non validée actuellement |
| `pickup_longitude` | number | obligatoire ; plage géographique non validée actuellement |

- Réponse : `ShopResponse`.
- `status` initial : `active`.
- Erreurs : `VALIDATION_ERROR`, `UNAUTHENTICATED`.

### `GET /v1/shops/mine`

- Auth : `JWT vendeur`.
- Paramètres : aucun.
- Réponse : `{ "items": [ShopResponse] }`.

### `GET /v1/shops/{shop_id}`

- Auth : aucune lecture publique.
- Réponse : `ShopResponse`.
- Champs : `id`, `owner_id`, `name`, `pickup_address`,
  `pickup_latitude`, `pickup_longitude`, `status`.
- Erreur : `NOT_FOUND` si la boutique n’existe pas.

## Catalogue et médias

### `GET /v1/catalog/categories`

- Auth : aucune.
- Réponse : `{ "items": [{"code": string, "name": string}] }`.
- Codes V1 : `fashion`, `beauty`, `home`, `electronics`, `food`, `books`,
  `sports`, `services`, `other`.
- Le champ produit reste compatible avec les anciennes valeurs texte ; les
  nouvelles créations doivent utiliser ces codes.

### `POST /v1/catalog/shops/{shop_id}/products`

- Auth : `JWT vendeur` propriétaire de `shop_id`.
- Corps :

| Champ | Type | Contraintes |
| --- | --- | --- |
| `title` | string | 1 à 200 caractères |
| `description` | string | défaut vide, maximum 5000 |
| `price_minor` | integer | `>= 0`, XOF |
| `stock` | integer | `>= 0` |
| `category` | string | 1 à 120 caractères |
| `photo_file_ids` | string[] | défaut `[]`; fichiers contrôlés par DiddiFiles |

- Réponse : `ProductResponse`.
- État initial : `draft`.
- Publication sans photo : actuellement autorisée.
- Erreurs : boutique inexistante/non propriétaire/suspendue, photo non
  confirmée ou mauvais `purpose`.

### `GET /v1/catalog/products`

- Auth : aucune.
- Query optionnelle : `category`, `search` (maximum 120 caractères).
- Réponse : `{ "items": [ProductResponse] }` avec produits publiés.

### `GET /v1/catalog/shops/{shop_id}/products`

- Auth : aucune.
- Query optionnelle : `category`, `search` (maximum 120 caractères).
- Réponse : `{ "items": [ProductResponse] }` avec produits publiés de la
  boutique.

### `GET /v1/catalog/my-products`

- Auth : `JWT vendeur`.
- Query optionnelle : `shop_id`.
- Réponse : `{ "items": [ProductResponse] }`.

### `GET /v1/catalog/products/{product_id}`

- Auth : aucune.
- Réponse : `ProductResponse`.

### `PATCH /v1/catalog/products/{product_id}`

- Auth : `JWT vendeur` propriétaire.
- Corps partiel : `title`, `description`, `price_minor`, `stock`, `category`.
- Les champs absents restent inchangés ; prix et stock doivent être `>= 0`.
- Réponse : `ProductResponse`.

### `POST /v1/catalog/products/{product_id}/publish`

- Auth : `JWT vendeur` propriétaire.
- Précondition : produit existant et boutique active.
- État produit : devient `published`.
- Réponse : `ProductResponse`.
- **À compléter :** aucune transition API `published -> paused/retired` n’est
  actuellement exposée ; aucune photo minimale n’est imposée.

### `POST /v1/catalog/products/{product_id}/photos/upload-session`

- Auth : `JWT vendeur` propriétaire.
- Corps : `filename` (1–255), `content_type` (1–120), `size_bytes` (`>0`).
- Réponse : `UploadSessionResponse` avec `file_id`, `status` et
  `upload.method/url/expires_in_seconds/headers`.
- Le frontend fait ensuite `PUT upload.url` avec les headers retournés.
- **À compléter :** taille maximale et formats MIME autorisés ne sont pas
  bloqués par DiddiShop ; ils dépendent de DiddiFiles jusqu’à validation du
  contrat.

### `POST /v1/catalog/products/{product_id}/photos`

- Auth : `JWT vendeur` propriétaire.
- Corps : `{ "file_id": string }` non vide.
- DiddiShop confirme le fichier auprès de DiddiFiles, vérifie le `purpose`
  `diddishop_product_image`, puis attache le fichier.
- Réponse : `ProductResponse`.
- **À compléter :** nombre maximal de photos non imposé localement.

### `GET /v1/catalog/products/{product_id}/photos`

- Auth : aucune.
- Réponse : `{ "items": [{"file_id": string, "url": string}] }`.
- Les listes produits remplissent aussi `photo_urls` lorsqu’une URL DiddiFiles
  est disponible.

### Forme `ProductResponse`

`id`, `shop_id`, `title`, `description`, `price_minor`, `currency`, `stock`,
`category`, `status`, `photo_file_ids`, `photo_urls`.

## Panier

### `GET /v1/cart`

- Auth : `JWT` ; `anonymous` en développement uniquement.
- Réponse : `CartResponse` contenant `id`, `customer_id`, `currency`, `lines`,
  `line_count`.
- Une ligne contient actuellement `product_id`, `shop_id`, `quantity`.
- **À compléter :** titre, prix unitaire, total de ligne, sous-total boutique
  et total checkout ne sont pas encore dans cette réponse.

### `POST /v1/cart/lines`

- Auth : `JWT`.
- Corps : `{ "product_id": string, "quantity": integer }` avec `quantity > 0`.
- Le produit doit exister, être `published` et disponible.
- Si la ligne existe, la quantité est augmentée.
- Réponse : `CartResponse`.

### `DELETE /v1/cart/lines/{product_id}`

- Auth : `JWT`.
- Supprime toute la ligne du produit.
- Réponse : `CartResponse`.
- Erreur : `CONFLICT` si la ligne n’existe pas.

## Checkout et paiement

### `POST /v1/checkouts`

- Auth : `JWT`.
- Corps :

| Champ | Type | Contraintes actuelles |
| --- | --- | --- |
| `idempotency_key` | string | obligatoire ; stabilité requise pour un rejeu |
| `recipient_name` | string? | facultatif actuellement |
| `recipient_phone` | string? | facultatif ; format non validé |
| `recipient_email` | string? | facultatif ; format non validé |
| `dropoff_address` | string? | facultatif actuellement |
| `dropoff_latitude` | number? | facultatif actuellement |
| `dropoff_longitude` | number? | facultatif actuellement |
| `rewards_campaign_id` | UUID? | facultatif |

- Le panier doit être non vide ; les produits doivent être publiés et le stock
  suffisant.
- Le checkout regroupe les lignes par boutique, calcule le devis DiddiSend,
  réserve éventuellement Rewards, décrémente le stock et crée un PaymentIntent.
- Réponse : `CheckoutResponse` avec `id`, `customer_id`, `total_minor`,
  `currency`, `status`, `order_ids`, `payment`.
- `payment` contient `payment_intent_id`, `amount_minor`, `currency`, `status`
  et relaie éventuellement `payment_url`, `checkout_url` ou `client_secret`.
- **À compléter :** route de devis avant paiement, ventilation par boutique,
  frais livraison détaillés, route de lecture checkout et route de retry.
- **À corriger avant staging authentifié :** une commande physique devrait
  exiger adresse de livraison et téléphone valides ; ce n’est pas encore le cas.

### `GET /v1/orders`

- Auth : `JWT`.
- Réponse : `{ "items": [OrderResponse] }` pour l’acheteur.

### `GET /v1/orders/{order_id}`

- Auth : lecture non protégée par dépendance d’acteur dans le code actuel.
- Réponse : `OrderResponse`.
- **À corriger :** vérifier que l’acheteur, le vendeur concerné ou un opérateur
  autorisé possède la commande avant exposition staging.

### `GET /v1/orders/seller/to-confirm`

- Auth : `JWT vendeur`.
- Réponse : `{ "items": [OrderResponse] }` limité aux commandes `TO_CONFIRM`.

### `POST /v1/orders/{order_id}/confirm`

- Auth : dépendance vendeur à ajouter avant staging ; non vérifiée actuellement.
- Précondition métier : commande `TO_CONFIRM`.
- Transition : `TO_CONFIRM -> TO_PREPARE`.
- Réponse : `OrderResponse`.

### `POST /v1/orders/{order_id}/ready`

- Auth : dépendance vendeur à ajouter avant staging ; non vérifiée actuellement.
- Précondition : commande `TO_PREPARE` ou commande déjà `READY_FOR_PICKUP` pour
  un rejeu.
- Transition : `TO_PREPARE -> READY_FOR_PICKUP`.
- Effet : DiddiShop appelle DiddiSend avec
  `shop:create-delivery:{order_id}:1` et persiste `delivery_id`.
- Réponse : `OrderResponse`.

### `POST /v1/orders/{order_id}/transitions`

- Auth : dépendance d’acteur à ajouter avant staging ; non vérifiée actuellement.
- Query obligatoire : `target`, valeur de `FulfillmentStatus`.
- Valeurs : `PAYMENT_PENDING`, `TO_CONFIRM`, `TO_PREPARE`, `READY_FOR_PICKUP`,
  `PICKED_UP`, `IN_TRANSIT`, `DELIVERED`, `RETURNED`, `CANCELLED`, `FAILED`,
  `DISPUTED`, `CLOSED`.
- Réponse : `OrderResponse`.
- La machine refuse les transitions non présentes dans la table des états.

### Forme `OrderResponse`

`id`, `shop_id`, `checkout_id`, `total_minor`, `currency`,
`fulfillment_status`, `payment_status`, `delivery_id`, `version`,
`payment_intent_id`, `items`.

- `items` contient actuellement au minimum `product_id`, `title`,
  `unit_price_minor`, `quantity` dans le snapshot interne.
- **À compléter :** `line_total`, sous-total, `created_at`, échéance vendeur,
  adresse/quartier et acheteur sont à formaliser.

## Livraison DiddiSend

### `POST /v1/deliveries/orders/{order_id}`

- Auth : route de reprise interne à protéger par opérateur/S2S avant staging.
- Précondition : commande `READY_FOR_PICKUP`.
- Idempotence : projection existante renvoyée ; clé externe
  `shop:create-delivery:{order_id}:1`.
- Réponse actuelle : projection `id`, `order_id`, `status`, `proof_ref`,
  `tracking`.
- Le frontend vendeur ne doit pas appeler cette route ; il appelle `/ready`.

### `GET /v1/deliveries/orders/{order_id}`

- Auth : route de lecture à protéger par acheteur/vendeur/opérateur avant
  staging.
- Réponse actuelle : projection ou
  `{ "order_id": string, "status": "not_requested" }`.
- Projection : `id`, `order_id`, `status`, `proof_ref`, `tracking`.
- **À compléter :** coursier, code de remise, position et contrat détaillé de
  `tracking` restent la propriété DiddiSend et doivent être projetés si le
  frontend les nécessite.

## Annulation et réclamations

### `POST /v1/claims/orders/{order_id}/cancel`

- Auth : dépendance acheteur à ajouter avant staging ; non vérifiée actuellement.
- Corps : `{ "reason": string }`, défaut `buyer_requested`, 1 à 500 caractères.
- Interdit après `PICKED_UP`, `IN_TRANSIT` ou `DELIVERED`.
- Effets : annulation, restauration du stock, annulation DiddiSend si possible,
  refund DiddiPay idempotent.
- Réponse actuelle : objet `Order` interne sérialisé.
- **À compléter :** `CancelOrderResponse` et codes détaillés
  `ORDER_NOT_CANCELLABLE`, `DELIVERY_ALREADY_PICKED_UP`, `REFUND_PENDING`.

### `POST /v1/claims/orders/{order_id}`

- Auth : `JWT`.
- Corps : `{ "reason": string }`, 1 à 2000 caractères.
- Précondition : commande `DELIVERED`, fenêtre de réclamation de 72 h,
  aucune réclamation ouverte.
- Réponse actuelle : `Claim` avec `id`, `order_id`, `customer_id`, `reason`,
  `opened_at`, `status`, `decision`, `amount_to_refund`, `decided_at`.

### `POST /v1/claims/{claim_id}/decision`

- Auth : route support/backoffice à protéger avant staging.
- Corps : `decision` dans `buyer|seller|partial|rejected` ;
  `amount_to_refund >= 0`.
- Réponse actuelle : `Claim`.
- Pour `buyer`/`partial`, le remboursement ne peut pas dépasser le total de la
  commande.

## Campagnes, backoffice et support

### `GET /v1/campaigns/active`

- Auth : aucune.
- Réponse actuelle : `{ "items": [], "source": "diddirewards", "mode": "projection_not_configured" }`.
- Ce n’est pas encore une projection de campagnes réellement configurée.

### `GET /v1/admin/shop/capabilities`

- Auth : administrateur, support ou service ; développement local toléré.
- Réponse : `service`, `owner`, `commands` et `note`.

### `GET /v1/admin/shop/orders/{order_id}`

- Auth : administrateur, support ou service.
- Réponse : `{ "order": Order, "delivery_projection": DeliveryProjection|null }`.
- Une entrée d’audit est écrite.

### `POST /v1/admin/shop/claims/{claim_id}/decision`

- Auth : administrateur, support ou service.
- Header obligatoire : `Idempotency-Key`.
- Corps : `decision`, `amount_to_refund >= 0`, `reason` de 1 à 1000 caractères.
- Rejeu même clé/même corps : réponse mémorisée ; même clé/corps différent :
  conflit.

### `GET /internal/v1/support/orders/{order_id}/context`

- Auth : réseau/S2S interne.
- Réponse : `order`, `delivery`, `claim`, `owner_service` et `source_of_truth`.
- Cette route renvoie actuellement `projection_not_configured` dans son mode
  simple.

### `GET /internal/v1/support/orders/{order_id}/context/live`

- Auth : réseau/S2S interne.
- Réponse : même contexte enrichi par les projections locales.

### `POST /internal/v1/support/orders/{order_id}/cases`

- Auth : `JWT` dans le code actuel ; accès réseau/S2S à formaliser.
- Corps : aucun JSON ; le contexte commande fournit la raison.
- Effet : création d’un cas DiddiSupport avec la clé
  `shop:claim-case:{order_id}:1`.

### Routes de santé internes

| Route | Réponse actuelle |
| --- | --- |
| `GET /internal/v1/comms/health` | `owner`, `consumer` |
| `GET /internal/v1/observability/health` | `service`, `status`, `telemetry` |
| `GET /internal/v1/rewards/health` | `owner`, `consumer`, `mode` |

Ces routes sont des sondes internes et ne doivent pas être exposées au frontend.

## Webhooks entrants

### `POST /internal/v1/webhooks/diddipay`

- Auth : signature `X-Webhook-Signature` calculée avec le secret DiddiPay.
- Corps : `ExternalEvent` : `event_id`, `event_type`, `event_version`,
  `aggregate_id`, `payload`, `correlation_id?`, `causation_id?`.
- Réponse : `{ "status": "processed" }` ou `{ "status": "duplicate" }`.
- Déduplication : inbox `diddishop-diddipay` par `event_id`.
- Événements métier consommés : `payment.succeeded`, `payment.failed`,
  `payment.refunded`, `seller.release.completed`.

### `POST /internal/v1/webhooks/diddisend`

- Auth : signature DiddiSend obligatoire.
- Corps : même `ExternalEvent`.
- Réponse : `processed` ou `duplicate`.
- Déduplication : inbox `diddishop-diddisend` par `event_id`.
- Événements : `delivery.created`, `delivery.assigned`,
  `delivery.picked_up`, `delivery.in_transit`, `delivery.delivered`,
  `delivery.failed`, `delivery.returned`.

## Contrats non HTTP

- Aucun WebSocket n’est implémenté.
- Les événements sortants utilisent l’enveloppe `EventEnvelope` avec
  `event_id`, `event_type`, `event_version`, `occurred_at`, `producer`,
  `aggregate_type`, `aggregate_id`, `correlation_id`, `causation_id` et
  `payload`.
- L’outbox est au moins une fois ; l’inbox déduplique les événements entrants.
- Les retries externes utilisent la même clé après lecture de l’état externe.
- DiddiObserve reçoit uniquement OTLP HTTP/protobuf ; les logs ne contiennent
  ni secrets, tokens, cookies, données de paiement sensibles ni corps complets.

## Limites explicitement non couvertes

Les points suivants ne doivent pas être inventés par le frontend :

1. aucun temps réel WebSocket ;
2. aucun catalogue de formats photo validé côté DiddiShop ;
3. aucun maximum de photos produit ;
4. aucune échéance vendeur exposée dans `OrderResponse` ;
5. aucune route publique de devis ou de reprise paiement ;
6. aucune garantie que `GET /v1/orders/{order_id}`, `/ready`, `/confirm`,
   `/transitions` et les routes livraison/annulation soient correctement
   autorisées en staging tant que leurs dépendances d’acteur ne sont pas
   ajoutées.
