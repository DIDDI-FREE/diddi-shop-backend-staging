# Journal S13 — 2026-11-25

## Contrats vérifiés

- DiddiPay : `/payment-intents`, `/cancel` et `/refunds` présents dans
  l’OpenAPI staging. Le payload attend `amount`; la réponse utilise `id`.
  L’adaptateur normalise maintenant vers `payment_intent_id` et `refund_id`.
- DiddiSend : quote, création et annulation présentes ; le payload accepte
  `origin_module=diddishop`, `payment_method=diddipay`, `prepaid_by_origin` et
  `quoted_price`.
- DiddiFiles : upload-session, confirmation, metadata, download-url et
  public-url présents.
- DiddiRewards : routes dédiées DiddiShop quote/reserve/confirm/correct
  présentes.
- DiddiComms : route conversation présente sans corps JSON.
- DiddiSupport : routes internal case/context présentes ; `/health` public
  répond 404 et ne doit pas être utilisé comme preuve de contrat.

## Vérifications locales

- `ruff check .` : OK
- `pytest -q` : OK, 55 tests
- `python -m compileall -q app_base tests alembic` : OK
- `docker compose config --quiet` : OK
- `docker compose up -d --build` : impossible, Docker Desktop ne démarre pas
  son daemon.

## Déploiement en attente

Relancer le Compose lorsque Docker Desktop est opérationnel, puis vérifier
`/health`, `/ready`, PostgreSQL, Redis et les migrations. Les appels staging
authentifiés restent à exécuter avec les secrets provisionnés, sans utiliser
de transaction financière réelle pour la recette initiale.
