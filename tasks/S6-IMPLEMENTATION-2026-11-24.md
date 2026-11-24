# Journal S6 — 2026-11-24

## Réalisé

- Idempotence des opérations cancel/refund/release au niveau commande.
- Refund automatique contrôlé sur `delivery.failed` et `delivery.returned`.
- Protection contre les refunds supérieurs au total de commande.
- Fenêtre de réclamation et transition `DISPUTED` conservées.
- Traitement des timestamps persistés sous forme ISO.

## Vérifications

- `35 passed`
- `ruff check .` OK
- compilation Python OK

## Blocage documenté

- La release vendeur ne doit pas appeler le payout générique DiddiPay. Le
  contrat marketplace hold/release reste à confirmer.
