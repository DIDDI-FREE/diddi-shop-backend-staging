# Contrats inter-services à valider

## DiddiSend

Base staging observée : `https://diddisend-api-staging.diddifree.com`.
Routes observées : `/health`, `/openapi.json`, `/v1/deliveries/quote`,
`/v1/deliveries`, `/v1/deliveries/{delivery_id}`,
`/v1/deliveries/{delivery_id}/cancel`.

`POST /v1/deliveries` doit accepter le contrat DiddiFood adapté :
`origin_module=diddishop`, `order_reference`, credential S2S, pickup, dropoff,
package, `quoted_price`, `financial_breakdown`, `payment_method=diddipay` et
`Idempotency-Key`. DiddiSend ne doit pas créer un second PaymentIntent pour un
checkout déjà payé par DiddiShop.

Le schéma staging observé expose encore une ventilation financière Food en XOF.
À confirmer pour DiddiShop : ventilation XAF, `prepaid_by_origin=true` et
événements signés de suivi.

## DiddiPay

Base staging observée : `https://pay-api-staging.diddifree.com/payfund/v1`.
Pour le MVP V1, DiddiShop utilise uniquement PaymentIntent, annulation,
remboursement et événements signés. La séquestration marketplace et la release
vendeur sont reportées en V2. Elles devront faire l’objet d’un contrat séparé
avant activation ; le payout existant ne doit pas être considéré comme une
release vendeur.

## DiddiFiles

Routes observées : upload-session, confirmation, métadonnées, download-url et
public-url. Confirmer la lecture par URL signée du purpose
`diddishop_product_image` et la politique de visibilité finale.

## DiddiFreeID

Route de token : `POST /identity/v1/auth/service/token`, avec
`grant_type=client_credentials`, `client_id`, `client_secret`, `audience` et
`scope` en `application/x-www-form-urlencoded`. DiddiShop implémente un client
distinct par cible, un token court mis en cache jusqu’à expiration et le header
`X-Client-ID` correspondant.

Provisionner un client DiddiShop distinct pour chaque service appelé, avec ses
scopes dédiés. Les secrets ne doivent jamais être committés.

## DiddiComms

Route observée : `POST /comms/v1/tasks/{owner_service}/{task_type}/{task_id}/conversation`.
Confirmer enveloppe, scopes, événements de livraison et comportement de retry.

## DiddiSupport

Routes observées : `POST /support/v1/internal/cases` et
`GET /support/v1/internal/context/{origin_service}/{resource_type}/{resource_id}`.
Confirmer enveloppe, scopes et statuts de dossier.

## DiddiObserve

L’URL `https://logs-otel.diddifree.com` a répondu `502` lors de l’observation.
Confirmer l’endpoint OTLP/logs/métriques/traces et son scope S2S après
rétablissement.
