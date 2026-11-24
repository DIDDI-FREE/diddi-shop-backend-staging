# Journal S8 — 2026-11-24

## Réalisé

- Autorisation admin/support/service sur les routes DiddiBackoffice.
- Idempotence HTTP des décisions sensibles par `Idempotency-Key`.
- Audit écrit en mémoire en local et PostgreSQL hors développement.
- Endpoint `/ready` avec état PostgreSQL/Redis séparé.
- Tests de sécurité et de replay de commande ajoutés.

## Vérifications

- `39 passed`
- `ruff check .` OK
- compilation Python OK
- `alembic upgrade head --sql` OK

## Vérifications staging encore nécessaires

- PostgreSQL et Redis disponibles.
- Migrations appliquées.
- Credentials/scopes S2S injectés.
- Contrats DiddiPay/DiddiSend/DiddiFiles validés.
- DiddiObserve rétabli et testé.
