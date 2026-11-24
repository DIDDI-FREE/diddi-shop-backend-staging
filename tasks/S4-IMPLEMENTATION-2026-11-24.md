# Journal S4 — 2026-11-24

## Réalisé

- Référence du PaymentIntent copiée dans chaque snapshot de commande.
- Adapter DiddiPay complété pour refund et annulation d’intention.
- Correction des refunds de réclamation pour ne plus utiliser le checkout à
  la place du PaymentIntent.
- Instance unique de `OrderService` exposée au runtime et aux webhooks.

## Vérifications

- `32 passed`
- `ruff check .` OK
- compilation Python OK

## Déploiement en attente

- Confirmer les schémas exacts DiddiPay pour PaymentIntent/refund.
- Configurer la signature callback et tester un webhook réel.
- Ne pas activer la release vendeur avant contrat marketplace signé.
