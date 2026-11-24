# PHASE 7B — observabilité et audit

**Statut :** terminé

Les appels externes sont conçus pour recevoir les IDs de corrélation, les
événements d’audit conservent acteur/ressource/cause et les tests ne loguent
aucun secret. Les métriques/exports réels restent dépendants du protocole
DiddiObserve de staging.

```text
python -m compileall -q app_base tests alembic
pytest -q
18 passed
```
