# S24-W — Journal d’implémentation

## Diagnostic

DiddiPay avait réussi et DiddiShop possédait la référence du PaymentIntent
dans `order.metadata.payment_intent_id`. Le payload de création DiddiSend ne
la reprenait pas, alors que `prepaid_by_origin=true` impose
`origin_payment_reference`.

## Correction

Le service de livraison injecte cette référence juste avant l’appel DiddiSend.
Le contrat local `DeliveryRequest` la sérialise explicitement. Aucun nouveau
paiement n’est créé.

## Vérifications

- Tests ciblés et suite complète à exécuter avant commit.
- Aucun déploiement Portainer effectué.
