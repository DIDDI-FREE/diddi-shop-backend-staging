# S9-A — Tokens DiddiFreeID `client_credentials`

## Réalisé

- ajout de `ServiceTokenProvider` avec appel form-urlencoded au contrat
  `POST /identity/v1/auth/service/token` ;
- cache mémoire court et verrou asynchrone contre les demandes concurrentes ;
- ajout des maps `service_client_ids` et `service_client_secrets` ;
- création d’un provider par intégration avec audience et scopes propres ;
- transmission de `Authorization: Bearer` et `X-Client-ID` ;
- refus fail-closed en environnement non développement ;
- tests de cache, audience, scopes, headers et validation de configuration.

## Vérifications

- `pytest -q` : 42 passed ;
- `ruff check .` : OK ;
- `python -m compileall -q app_base tests alembic` : OK ;
- `git diff --check` : OK.

## Déploiement en attente

Provisionner les sept clients DiddiFreeID et leurs secrets dans le secret
manager staging, puis exécuter les tests de fumée vers chaque service cible.
