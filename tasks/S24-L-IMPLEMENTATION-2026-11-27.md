# S24-L — Propagation de `customer_phone`

## Diagnostic

Le checkout validait `recipient_phone`, mais le contrat PaymentIntent ne le
transportait pas. DiddiPay ne pouvait donc pas fournir `customer_phone` à
PawaPay, qui rejetait le dépôt avant tout appel fournisseur.

## Implémentation

- Ajout de `customer_phone` à `PaymentIntentCommand`.
- Transmission vers DiddiPay dans le payload PaymentIntent.
- Conservation dans le paiement du checkout pour les retries.
- Test du contrat HTTP avec un téléphone camerounais au format international.
- Correction de compatibilité des retries historiques : si `payment.customer_phone`
  est absent, le téléphone est récupéré depuis
  `order.metadata.delivery_request.recipient_phone`.
- Ajout d’un test de régression couvrant un checkout historique Orange Money.

## Vérifications

- `pytest -q` : 90 passed.
- `ruff check .` : OK.
- Déploiement Portainer : manuel par l’utilisateur uniquement.
