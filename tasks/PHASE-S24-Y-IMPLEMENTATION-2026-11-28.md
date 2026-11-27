# Journal S24-Y — 2026-11-28

## Correction

La création PaymentIntent utilise `diddishop:checkout:{checkout_id}`. La
livraison DiddiShop envoyait auparavant `shop-order:{order_id}`, incompatible
avec la vérification stricte DiddiPay. La commande conserve maintenant la
référence PaymentIntent et la réutilise dans `order_reference`.

Les callbacks DiddiSend utilisant cette référence sont résolus vers l’unique
commande du checkout. Les checkouts multi-boutiques sont refusés pour ce cas,
car le contrat ne permet pas d’associer un PaymentIntent unique à plusieurs
livraisons de façon non ambiguë.

## Vérifications

- Tests ciblés : 11 passed.
- Lint ciblé : OK.
- Déploiement et rejeu staging : à effectuer manuellement.
