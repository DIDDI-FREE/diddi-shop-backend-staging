# Contrats inter-services à valider

## DiddiSend

`POST /v1/deliveries` doit accepter le contrat DiddiFood adapté :
`origin_module=diddishop`, `order_reference`, credential S2S, pickup, dropoff,
package, `quoted_price`, `financial_breakdown`, `payment_method=diddipay` et
`Idempotency-Key`. DiddiSend ne doit pas créer un second PaymentIntent pour un
checkout déjà payé par DiddiShop.

## DiddiPay

Confirmer l’API marketplace de hold/release vendeur, refund partiel, scopes et
événements signés. Le payout existant ne doit pas être considéré comme une
release vendeur sans contrat métier explicite.

## DiddiFiles

Confirmer la lecture par URL signée du purpose `diddishop_product_image`.

## DiddiFreeID

Provisionner un client DiddiShop et des scopes séparés pour chaque service
appelé. Les secrets ne doivent jamais être committés.

## DiddiObserve, DiddiComms et DiddiSupport

Confirmer les endpoints d’export, de création de tâches et d’ouverture de cas,
ainsi que leurs enveloppes et scopes S2S.
