# PHASE 1A — journal de fondations

**Statut :** terminé

Le dépôt local a été initialisé. Le remote GitHub fourni répond actuellement
`Repository not found`; ce point ne bloque pas les vérifications locales.

## Livrables

- configuration PostgreSQL/Redis ;
- modèles SQLAlchemy pour outbox, inbox, idempotence et audit ;
- migration Alembic réversible ;
- port/adaptateur Redis Streams et verrou ;
- middleware de corrélation ;
- scopes S2S dédiés ;
- tests de fondation.

## Vérification

```text
python -m compileall -q app_base tests alembic
pytest -q
4 passed
```
