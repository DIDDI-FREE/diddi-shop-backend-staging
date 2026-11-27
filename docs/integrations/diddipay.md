# Intégration DiddiPay

En V1, DiddiShop utilise DiddiPay pour PaymentIntent, annulation, refund et
événements de paiement. Aucun hold marketplace ni release vendeur n’est actif.

## Mapping observé

`POST /payfund/v1/payment-intents` attend `business_reference`, `amount` et
`currency=XOF`. L’adaptateur DiddiShop transforme son modèle interne
`amount_minor` vers `amount` et normalise la réponse `id` en
`payment_intent_id`.

Pour le mobile money, il envoie `channel=mobile_money` et traduit `wave` vers
`network=wave`, `mtn_momo` vers `network=mtn` et `orange_money` vers
`network=orange`. Les champs `payment_method` et `return_url` ne font pas
partie du schéma DiddiPay staging et ne sont pas envoyés.

Un refund attend `amount` et `reason`. La réponse `id` est normalisée en
`refund_id`. DiddiShop ne reçoit ni ne stocke de données carte.

## Idempotence et webhooks

- PaymentIntent : `shop:create-payment:{checkout_id}:1` ;
- refund : `shop:refund:{order_id}:{operation}` ;
- DiddiPay signe l'enveloppe JSON compacte et triée avec HMAC-SHA256, sur les
  octets réellement transmis, puis l'envoie dans `X-DiddiPay-Signature` ;
- DiddiShop vérifie cette signature avec `DIDDI_SHOP_DIDDIPAY_WEBHOOK_SECRET`;
- ce secret entrant est différent du credential S2S DiddiShop → DiddiPay ;
- l'enveloppe reçue est `{id, type, occurred_at, data}` et `data.business_reference`
  est de la forme `diddishop:checkout:{checkout_id}` ;
- un événement déjà traité retourne un résultat `duplicate` sans nouvelle
  mutation.

Les statuts locaux `PENDING`, `REFUNDED` et `PARTIALLY_REFUNDED` ne remplacent
pas les statuts fournisseurs : le mapping doit être explicite.

## V2

Le port de release vendeur reste désactivé en V1. Il ne sera activé qu’après
un contrat DiddiPay dédié pour hold, release, ledger, litiges, réconciliation
et événements.
