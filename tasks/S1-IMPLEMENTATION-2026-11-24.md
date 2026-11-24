# Journal S1 — 2026-11-24

## Réalisé

- Ajout de `SqlOutboxStore`, `SqlInboxStore` et `SqlIdempotencyStore`.
- Ajout de publication Redis Streams sur `diddishop.events.v1`.
- Retry exponentiel borné et remise en disponibilité des événements échoués.
- Ajout de la migration `0002_business_aggregates`.
- Ajout de repositories SQL par agrégat, sans accès direct entre modules.
- Sélection des repositories durables hors développement dans le lifespan.
- Conservation des doubles en mémoire pour les tests unitaires et le mode local.

## Vérifications

- `25 passed`
- `ruff check .` OK
- `python -m compileall -q app_base tests alembic` OK
- `alembic upgrade head --sql` OK

## Déploiement en attente

- Exécuter `alembic upgrade head` contre PostgreSQL staging.
- Configurer Redis Streams et le consumer group DiddiShop.
