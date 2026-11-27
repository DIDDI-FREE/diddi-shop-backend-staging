# S24-G — migrations au démarrage staging

## Diagnostic

Les migrations Alembic `0001_platform_foundation` et
`0002_business_aggregates` étaient présentes dans le dépôt et copiées dans
l’image, mais `docker-compose.yml` lançait directement Uvicorn. La base
PostgreSQL persistante n’avait donc pas la table `carts`, ce qui provoquait un
HTTP 500 après authentification sur `GET /v1/cart`.

## Comparaison des modules

- DiddiFood staging : `alembic upgrade head && exec python -m app.serve`.
- DiddiPay : migrations exécutées par l’entrypoint avant l’application.
- DiddiSupport : service `support-migrate` bloquant l’API et le worker.

## Implémentation

- `docker-compose.yml` exécute `alembic upgrade head` avant Uvicorn.
- Ajout d’un test qui vérifie la création du schéma complet, dont `carts`.
- Correction de nettoyage du logger OTLP : la propagation précédente est
  restaurée à l’arrêt, afin que les tests et les logs Docker ne restent pas
  silencieusement coupés après un cycle d’application.
- Runbook, statut et décisions mis à jour.

## Vérifications réalisées

- `pytest -q tests/test_migrations.py` : 1 test passé.
- `pytest -q` : 82 tests passés.
- `ruff check .` : OK.
- `python -m compileall -q app_base tests alembic` : OK.
- `docker compose -f docker-compose.local.yml config --quiet` : OK.
- `docker compose --env-file portainer.env -f docker-compose.yml config --quiet` : OK.
- Build de l’image API : OK.
- Test Docker local sur PostgreSQL vide : API healthy, HTTP `/health` 200,
  deux migrations appliquées, conteneurs API/PostgreSQL/Redis opérationnels.
- Le projet Docker temporaire et son volume ont été supprimés après le test.

## Déploiement

Aucun déploiement Portainer n’est effectué par Codex. L’utilisateur devra
déployer manuellement le nouveau Compose/image, puis vérifier les logs de
migration et rejouer `GET /v1/cart`.
