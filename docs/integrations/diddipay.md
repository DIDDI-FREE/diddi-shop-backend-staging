# Intégration DiddiPay

En V1, DiddiShop utilise DiddiPay pour PaymentIntent, annulation, refund et
événements de paiement. Aucun hold marketplace ni release vendeur n’est actif.

## Mapping observé

`POST /payfund/v1/payment-intents` attend `business_reference`, `amount` et
`currency=XOF`. L’adaptateur DiddiShop transforme son modèle interne
`amount_minor` vers `amount` et normalise la réponse `id` en
`payment_intent_id`.

Un refund attend `amount` et `reason`. La réponse `id` est normalisée en
`refund_id`. DiddiShop ne reçoit ni ne stocke de données carte.

## Idempotence et webhooks

- PaymentIntent : `shop:create-payment:{checkout_id}:1` ;
- refund : `shop:refund:{order_id}:{operation}` ;
- les webhooks sont signés avec le secret DiddiPay ;
- un événement déjà traité retourne un résultat `duplicate` sans nouvelle
  mutation.

Les statuts locaux `PENDING`, `REFUNDED` et `PARTIALLY_REFUNDED` ne remplacent
pas les statuts fournisseurs : le mapping doit être explicite.

## V2

Le port de release vendeur reste désactivé en V1. Il ne sera activé qu’après
un contrat DiddiPay dédié pour hold, release, ledger, litiges, réconciliation
et événements.
