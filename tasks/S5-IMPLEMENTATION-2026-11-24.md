# Journal S5 — 2026-11-24

## Réalisé

- Inspection de l’OpenAPI DiddiSend staging.
- Suppression du payload de quote spécifique inventé (`shop_id`/`lines`).
- Utilisation des schémas DiddiSend pour locations et packages.
- Propagation des adresses, identités et du package depuis le checkout.
- Confirmation du mode `diddipay` prépayé par l’origine.
- Sauvegarde de la relation commande/livraison après création.

## Vérifications

- `33 passed`
- `ruff check .` OK
- compilation Python OK

## Déploiement en attente

- Confirmer le contrat DiddiSend pour `prepaid_by_origin` et le breakdown
  financier DiddiShop/XAF.
- Tester quote/create/cancel avec un credential S2S staging.
