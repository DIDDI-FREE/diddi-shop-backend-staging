# S24-Y — Référence PaymentIntent et vérification coverage

## Objectif

Aligner la référence envoyée à DiddiSend sur la `business_reference` du
PaymentIntent, sans confondre le total payé avec le prix de livraison.

## Sous-lots

- [x] A — conserver la référence PaymentIntent sur la commande.
- [x] B — transmettre cette référence à DiddiSend et résoudre les callbacks.
- [x] C — tester le flux et documenter la limite multi-boutiques.

## Hors périmètre

Aucun changement dans DiddiPay, DiddiSend ou Portainer. Aucun second paiement.
