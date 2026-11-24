# Journal S12 — 2026-11-24

## S12-A à S12-C

- Ajout des alias Compose `OTEL_*`, `ENVIRONMENT`, `DEPLOYMENT_ID` et du
  composant de processus.
- Suppression de l’exigence de client/secret DiddiFreeID pour DiddiObserve.
- Ajout d’exporteurs OTLP HTTP/protobuf asynchrones avec files bornées, limites
  de taille, retry réseau/429/502/503/504, `Retry-After`, compteurs de pertes et
  rejets, timeout 5 secondes et flush borné.
- Ajout du resource set Diddi, de la corrélation traceparent/trace/span et de
  la propagation sur les appels sortants.
- Ajout du logger applicatif réel, du journal d’accès synthétique et du
  filtrage des champs confidentiels.

## Vérifications

- `python -m compileall -q app_base tests alembic` : OK
- `ruff check app_base tests` : OK
- `pytest -q` : OK, 50 tests
- tests PostgreSQL/Redis et déploiement : non exécutés, infrastructure et
  secrets hors dépôt.

## Déploiement en attente

Injecter `secrets/onboarding/diddishop.env` par Compose, déployer, transmettre
SHA/contact/marqueurs synthétiques API et worker, puis fournir les informations
Prometheus et le token de scrape dédié. Vérifier le refus/succès d’authentification,
la corrélation, l’absence de données sensibles et la panne collecteur sans
transaction réelle.
