# PHASE 2B — DiddiPay, DiddiFiles et DiddiSend

**Statut :** terminé

Les adaptateurs portent maintenant les credentials S2S et les headers de
corrélation. DiddiSend reprend le payload DiddiFood avec `origin_module`,
`order_reference`, `payment_method=diddipay`, `financial_breakdown` et
`prepaid_by_origin=true`. DiddiShop ne gère pas la flotte.
