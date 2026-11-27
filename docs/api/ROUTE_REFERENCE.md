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
| `Webhook` | DiddiPay : `X-DiddiPay-Signature` sur le corps exact, sans timestamp ; DiddiSend : `X-DiddiSend-Signature: sha256=<digest>` sur le corps exact, sans timestamp |
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
- Transitions disponibles : `draft -> published`, `paused -> published`,
  `published -> paused`, et `draft|published|paused -> retired`.
- Une photo n’est pas obligatoire pour publier en V1.

### `POST /v1/catalog/products/{product_id}/pause`

- Auth : `JWT vendeur` propriétaire.
- Précondition : produit `published`.
- Effet : passe le produit à `paused`, donc il disparaît du catalogue public
  et ne peut plus être ajouté au panier.
- Réponse : `ProductResponse`.

### `POST /v1/catalog/products/{product_id}/retire`

- Auth : `JWT vendeur` propriétaire.
- Précondition : produit existant ; le rejeu sur un produit déjà `retired` est
  idempotent.
- Effet : passe le produit à `retired`, état terminal côté catalogue.
- Réponse : `ProductResponse`.

### `POST /v1/catalog/products/{product_id}/photos/upload-session`

- Auth : `JWT vendeur` propriétaire.
- Corps : `filename` (1–255), `content_type` (1–120), `size_bytes` (`>0`).
- Réponse : `UploadSessionResponse` avec `file_id`, `status` et
  `upload.method/url/expires_in_seconds/headers`.
- Le frontend fait ensuite `PUT upload.url` avec les headers retournés.
- Contraintes DiddiShop : maximum `10 MiB` (`10_485_760` octets) et formats
  `image/jpeg`, `image/png`, `image/webp`.

### `POST /v1/catalog/products/{product_id}/photos`

- Auth : `JWT vendeur` propriétaire.
- Corps : `{ "file_id": string }` non vide.
- DiddiShop confirme le fichier auprès de DiddiFiles, vérifie le `purpose`
  `diddishop_product_image`, puis attache le fichier.
- Réponse : `ProductResponse`.
- Maximum local : `8` photos par produit. La confirmation DiddiFiles et le
  `purpose=diddishop_product_image` restent obligatoires.

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
  `line_count`, `subtotal_minor` et `shop_subtotals`.
- Une ligne contient `product_id`, `shop_id`, `quantity`, `title`,
  `unit_price_minor` et `line_total_minor`. Le frontend ne recalcule pas les
  montants : il affiche les valeurs du backend.

### `POST /v1/cart/lines`

- Auth : `JWT`.
- Corps : `{ "product_id": string, "quantity": integer }` avec `quantity > 0`.
- Le produit doit exister, être `published` et disponible.
- Si la ligne existe, la quantité est augmentée.
- Réponse : `CartResponse`.
- Stock insuffisant : HTTP `422`, code `INSUFFICIENT_STOCK`, avec
  `details.product_id`, `requested_quantity` et `available_quantity`.

### `DELETE /v1/cart/lines/{product_id}`

- Auth : `JWT`.
- Supprime toute la ligne du produit.
- Réponse : `CartResponse`.
- Erreur : `CONFLICT` si la ligne n’existe pas.

### `PATCH /v1/cart/lines/{product_id}`

- Auth : `JWT` acheteur.
- Corps : `{ "quantity": integer }` avec `quantity >= 1`.
- Effet : remplace la quantité de la ligne par la valeur demandée ; ce n’est
  pas une opération d’incrément.
- Le produit doit rester publié et la quantité ne peut pas dépasser le stock.
- `quantity=0` est refusé (`VALIDATION_ERROR`) ; utiliser `DELETE` pour
  supprimer la ligne.
- Réponse : `CartResponse` complet.
- L’opération est rejouable avec la même quantité.

## Checkout et paiement

### `POST /v1/checkouts`

- Auth : `JWT`.
- Corps :

| Champ | Type | Contraintes actuelles |
| --- | --- | --- |
| `idempotency_key` | string | obligatoire ; stabilité requise pour un rejeu |
| `recipient_name` | string | obligatoire, 1–160 caractères |
| `recipient_phone` | string | obligatoire, format E.164 `+<pays><numéro>` |
| `recipient_email` | string? | facultatif |
| `dropoff_address` | string | obligatoire, 1–500 caractères |
| `dropoff_latitude` | number | obligatoire, -90 à 90 |
| `dropoff_longitude` | number | obligatoire, -180 à 180 |
| `rewards_campaign_id` | UUID? | facultatif |

- Le panier doit être non vide ; les produits doivent être publiés et le stock
  suffisant.
- Le checkout regroupe les lignes par boutique, calcule le devis DiddiSend,
  réserve éventuellement Rewards, décrémente le stock et crée un PaymentIntent.
- Réponse : `CheckoutResponse` avec `id`, `customer_id`, `total_minor`,
  `subtotal_minor`, `delivery_fee_minor`, `discount_minor`,
  `shop_breakdowns`, `payment_attempt`, `currency`, `status`, `order_ids`,
  `created_at` et `payment`.
- `payment` contient `payment_intent_id`, `amount_minor`, `currency`, `status`,
  `payment_method`, `customer_phone`, `expires_at` et relaie éventuellement
  `payment_url`, `checkout_url`, `client_secret`,
  `payment_method`, `expires_at` et `next_action`. Le V1 accepte `wave`, `mtn_momo` et
  `orange_money`, avec `wave` par défaut. `return_url` est facultative et doit
  cibler `diddifree.com` ou un sous-domaine en HTTPS (port 443/default),
  sans credentials, fragment ni traversée de chemin, 1–2048 caractères.
  Elle est transmise comme `callback_url` DiddiPay. `return_target` (1–64
  caractères) est une alternative, jamais cumulable avec l'URL.
  Sans option, le backend utilise sa configuration, par défaut
  `https://diddishop-backend.diddifree.com/payments/return`.
  `next_action` est décrit dans [l'intégration DiddiPay](../integrations/diddipay.md).
  `requires_action` reste pending ; si l'action est `redirect`, ouvrir
  `payment.payment_url` (égal à `next_action.url`).
- Le téléphone est transmis à DiddiPay comme `customer_phone` et conservé
  côté backend pour le retry, sans être exposé dans `CheckoutResponse`.
- Header de réponse `Idempotency-Replayed` : `false` pour une création nouvelle,
  `true` pour la réponse mémorisée d'une même clé (aucun nouveau paiement).
- `POST /v1/checkouts/quote` calcule le sous-total, les frais DiddiSend par
  boutique et le total sans créer de paiement.
- `GET /v1/checkouts/{checkout_id}` lit l’état du checkout et de son paiement.
- `POST /v1/checkouts/{checkout_id}/retry` relance uniquement un checkout en
  `payment_failed`, avec une nouvelle `Idempotency-Key`. Le corps peut aussi
  fournir `payment_method` (`wave`, `mtn_momo` ou `orange_money`) pour changer
  de moyen après un échec.

### `POST /v1/checkouts/quote`

- Auth : `JWT` acheteur.
- Corps : adresse, latitude/longitude, nom et téléphone du destinataire ; les
  mêmes contraintes que la création checkout s’appliquent, sans clé
  d’idempotence.
- Effet : lecture du panier et devis DiddiSend par boutique ; aucun stock,
  ordre ou paiement n’est créé.
- Réponse : `CheckoutQuoteResponse` avec `currency`, sous-total, frais,
  remise, total et `shop_breakdowns`.

### `GET /v1/checkouts/{checkout_id}`

- Auth : `JWT` du client propriétaire ou opérateur.
- Réponse : `CheckoutResponse` avec le statut checkout et le paiement
  normalisé DiddiPay.

### `POST /v1/checkouts/{checkout_id}/retry`

- Auth : `JWT` du client propriétaire ou opérateur.
- Header obligatoire : `Idempotency-Key` ; il doit identifier cette tentative
  de paiement et ne doit pas être la clé de création initiale.
- Précondition : checkout en `payment_failed`.
- Effet : crée une nouvelle tentative DiddiPay pour le même montant XOF et
  passe temporairement le checkout à `payment_pending`, puis conserve le
  statut final renvoyé : `payment_pending`, `payment_failed` ou `payment_succeeded`.
- Le téléphone valide est récupéré du paiement sauvegardé ou des métadonnées
  de la commande historique. Aucun corps JSON ni répétition du téléphone requis.
- Corps JSON facultatif : `{"return_url":"https://app.diddifree.com/return"}`
  ou `{"return_target":"app"}` (target à provisionner chez Pay). Même validation
  qu'à la création, autres propriétés refusées. `{}` ou corps absent conserve
  la destination sauvegardée, puis utilise la configuration si elle manque.
  Une même clé avec une autre destination retourne `409 CONFLICT`.
- `422 PAYMENT_RETURN_REQUIRED` ou `PAYMENT_RETURN_INVALID` : destination
  absente ou configuration invalide, sans nouvel appel ni incrément.
  Un corps invalide retourne `422 VALIDATION_ERROR`.
- `422 PAYMENT_PHONE_REQUIRED` : aucun téléphone valide enregistré. Aucun
  appel DiddiPay, incrément de tentative ou changement de clé n'est effectué.
  Ce cas exige de retrouver la donnée manquante, pas de répéter le paiement.
- Réponse : `CheckoutResponse`, avec header `Idempotency-Replayed`.
  `true` signifie que la réponse précédente a été rejouée : `payment_attempt`
  reste identique, aucun nouvel appel DiddiPay. Une nouvelle tentative après
  échec confirmé exige une clé jamais utilisée et retourne `false`.
  Le header est accessible au navigateur via CORS et décrit dans OpenAPI.

### `GET /payments/return`

- Auth : publique, aucun Bearer requis pour le retour du navigateur PawaPay.
- Corps/paramètres : aucun ; tout paramètre de requête est ignoré, non reflété.
- Réponse `200 text/html` : invite à revenir dans l'application pour consulter
  le paiement. `Cache-Control: no-store`, CSP restrictive, aucune redirection.
- Aucun appel fournisseur, aucune lecture de données privées, aucune mutation.
  Ce n'est **pas** le webhook HMAC et ce n'est jamais une preuve de paiement.

### `GET /v1/orders`

- Auth : `JWT`.
- Query : `limit` de 1 à 100 (défaut 20) et `cursor` opaque facultatif.
- Réponse : `{ "items": [OrderResponse], "next_cursor": string|null }` pour
  l’acheteur. Les éléments sont triés du plus récent au plus ancien.
- `OrderResponse` expose `created_at`, `delivered_at` et `status_history` ;
  chaque entrée d’historique contient `from`, `to`, `reason`, `actor`,
  `version` et `occurred_at`.

### `GET /v1/orders/{order_id}`

- Auth : `JWT` ; accès limité à l’acheteur, au vendeur de la boutique ou à un
  opérateur `admin/support/service`.
- Réponse : `OrderResponse`.

### `GET /v1/orders/seller/to-confirm`

- Auth : `JWT vendeur`.
- Réponse : `{ "items": [OrderResponse] }` limité aux commandes `TO_CONFIRM`.

### `POST /v1/orders/{order_id}/confirm`

- Auth : `JWT vendeur` propriétaire de la boutique.
- Précondition métier : commande `TO_CONFIRM`.
- Transition : `TO_CONFIRM -> TO_PREPARE`.
- Réponse : `OrderResponse`.

### `POST /v1/orders/{order_id}/ready`

- Auth : `JWT vendeur` propriétaire de la boutique.
- Précondition : commande `TO_PREPARE` ou commande déjà `READY_FOR_PICKUP` pour
  un rejeu.
- Transition : `TO_PREPARE -> READY_FOR_PICKUP`.
- Effet : DiddiShop appelle DiddiSend avec
  `shop:create-delivery:{order_id}:1` et persiste `delivery_id`.
- Réponse : `OrderResponse`.

### `POST /v1/orders/{order_id}/transitions`

- Auth : `JWT` acheteur, vendeur ou opérateur selon la transition.
- Query obligatoire : `target`, valeur de `FulfillmentStatus`.
- Valeurs : `PAYMENT_PENDING`, `TO_CONFIRM`, `TO_PREPARE`, `READY_FOR_PICKUP`,
  `PICKED_UP`, `IN_TRANSIT`, `DELIVERED`, `RETURNED`, `CANCELLED`, `FAILED`,
  `DISPUTED`, `CLOSED`.
- Réponse : `OrderResponse`.
- La machine refuse les transitions non présentes dans la table des états.

### Forme `OrderResponse`

`id`, `shop_id`, `checkout_id`, `total_minor`, `currency`,
`fulfillment_status`, `payment_status`, `delivery_id`, `version`,
`payment_intent_id`, `items`, `subtotal_minor`, `delivery_fee_minor`,
`discount_minor`, `created_at`, `seller_confirmation_deadline`,
`recipient_name` et `dropoff_address`.

- `items` contient `product_id`, `title`, `unit_price_minor`, `quantity` et
  `line_total_minor`. Le délai vendeur est fixé à 24 heures par défaut et est
  exposé dans `seller_confirmation_deadline`.

## Livraison DiddiSend

### `POST /v1/deliveries/orders/{order_id}`

- Auth : `JWT` opérateur (`admin/support/service`) ; le frontend vendeur ne
  l’appelle pas.
- Précondition : commande `READY_FOR_PICKUP`.
- Idempotence : projection existante renvoyée ; clé externe
  `shop:create-delivery:{order_id}:1`.
- Réponse : `DeliveryResponse` avec `id`, `order_id`, `status`, `proof_ref`,
  `tracking`, `courier`, `dropoff_code` et `position`.
- Le frontend vendeur ne doit pas appeler cette route ; il appelle `/ready`.

### `GET /v1/deliveries/orders/{order_id}`

- Auth : route de lecture à protéger par acheteur/vendeur/opérateur avant
  staging.
- Réponse actuelle : projection ou
  `{ "order_id": string, "status": "not_requested" }`.
- Projection : `id`, `order_id`, `status`, `proof_ref`, `tracking`.
- DiddiSend reste la source de vérité de ces champs ; DiddiShop ne fait que les
  projeter dans son contrat de lecture.

## Annulation et réclamations

### `POST /v1/claims/orders/{order_id}/cancel`

- Auth : `JWT` acheteur, vendeur ou opérateur autorisé.
- Corps : `{ "reason": string }`, défaut `buyer_requested`, 1 à 500 caractères.
- Interdit après `PICKED_UP`, `IN_TRANSIT` ou `DELIVERED`.
- Effets : annulation, restauration du stock, annulation DiddiSend si possible,
  refund DiddiPay idempotent.
- Réponse : `OrderResponse`.
- Erreurs stables : `DELIVERY_ALREADY_PICKED_UP` après enlèvement, et
  `ORDER_NOT_CANCELLABLE` après transit/livraison. Une annulation acceptée
  expose `payment_status=REFUND_PENDING` jusqu’à confirmation DiddiPay.

### `POST /v1/claims/orders/{order_id}`

- Auth : `JWT`.
- Corps : `reason_code` dans `not_as_described|damaged|incomplete|missing_item|other`,
  `reason` texte facultatif et au maximum trois `evidence_file_ids`.
- Précondition : commande `DELIVERED`, fenêtre de réclamation de 72 h,
  aucune réclamation ouverte.
- Réponse : `ClaimResponse` avec le motif, les preuves, `delivered_at`,
  `claim_deadline`, la décision, le montant et l’état du remboursement.

### `GET /v1/claims/orders/{order_id}`

- Auth : acheteur, vendeur de la boutique ou opérateur.
- Réponse : `ClaimResponse` pour la réclamation la plus récente de la commande.
- Erreur : `NOT_FOUND` si aucune réclamation n’existe.

### `POST /v1/claims/orders/{order_id}/evidence/upload-session`

- Auth : acheteur autorisé sur la commande.
- Corps : `filename`, `content_type` (`image/jpeg`, `image/png` ou
  `image/webp`) et `size_bytes` jusqu’à 10 MiB.
- Réponse : `UploadSessionResponse`. Le frontend upload vers l’URL signée,
  puis envoie le `file_id` dans `evidence_file_ids` lors de l’ouverture.
- Maximum : trois photos par réclamation. Le purpose DiddiFiles est
  `diddishop_claim_evidence`.

### `POST /v1/claims/{claim_id}/decision`

- Auth : route support/backoffice à protéger avant staging.
- Corps : `decision` dans `buyer|seller|partial|rejected` ;
  `amount_to_refund >= 0`.
- Réponse actuelle : `Claim`.
- Pour `buyer`/`partial`, le remboursement ne peut pas dépasser le total de la
  commande.
- Le frontend reçoit `refund_status`, `refund_method`, `refund_reference_masked`
  et `refunded_at` lorsqu’ils sont disponibles. Le numéro de téléphone complet
  n’est jamais exposé.
- `refund_status` vaut `not_requested`, `pending`, `processing`, `succeeded` ou
  `failed`, en minuscules. `refund_method` reprend `wave`, `mtn_momo` ou
  `orange_money` lorsqu’il est connu.

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

- Auth : acteur service S2S en staging/production ; le mode développement
  accepte l’acteur local de test.
- Corps : aucun JSON ; le contexte commande fournit la raison.
- Effet : création d’un cas DiddiSupport avec la clé
  `shop:claim-case:{order_id}:1`.
- Réponse : `SupportCaseResponse` sous la forme `{ "case": { ... } }` ; le
  contenu interne du cas reste celui retourné par DiddiSupport.

### Routes de santé internes

| Route | Réponse actuelle |
| --- | --- |
| `GET /internal/v1/comms/health` | `owner`, `consumer` |
| `GET /internal/v1/observability/health` | `service`, `status`, `telemetry` |
| `GET /internal/v1/rewards/health` | `owner`, `consumer`, `mode` |

Ces routes sont des sondes internes et ne doivent pas être exposées au frontend.

## Webhooks entrants

### `POST /internal/v1/webhooks/diddipay`

- Auth : HMAC-SHA256 dans `X-DiddiPay-Signature`, calculé par DiddiPay sur les
  octets exacts du corps JSON avec le secret partagé configuré dans
  `DIDDI_SHOP_DIDDIPAY_WEBHOOK_SECRET`. Aucun timestamp n'est utilisé.
- Corps DiddiPay : `{ "id", "type", "occurred_at", "data" }`. `data.business_reference`
  doit suivre `diddishop:checkout:{checkout_id}` ou `data` doit fournir
  `checkout_id`, `order_id` ou `order_ids`. L'ancien `ExternalEvent` reste accepté
  pour compatibilité interne.
- Réponse : `{ "status": "processed" }` ou `{ "status": "duplicate" }`.
- Déduplication : inbox `diddishop-diddipay` par `event_id`.
- Événements métier consommés : `payment.succeeded`, `payment.failed`,
  `payment.refunded`, `seller.release.completed`.

### `POST /internal/v1/webhooks/diddisend`

- Auth : HMAC-SHA256 dans `X-DiddiSend-Signature`, avec le préfixe
  `sha256=`, calculé sur les octets exacts du corps avec
  `DIDDI_SHOP_DIDDISEND_WEBHOOK_SECRET`. Aucun timestamp n'est utilisé.
- Corps DiddiSend : `{event_id, event_version, event_type, source_service,
  delivery_id, order_reference, status, origin_module, currency,
  financial_breakdown, occurred_at, data}`. `order_reference` doit suivre
  `shop-order:{order_id}` ou `data` doit fournir `order_id`.
- Réponse : `{ "status": "processed" }` ou `{ "status": "duplicate" }`.
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
2. les détails opérationnels de `tracking`, `courier`, `position` et
   `dropoff_code` restent ceux fournis par DiddiSend ;
3. les URLs de paiement optionnelles dépendent du résultat DiddiPay ;
4. les credentials, scopes S2S, PostgreSQL, Redis et OTLP doivent encore être
   vérifiés sur l’environnement staging.
