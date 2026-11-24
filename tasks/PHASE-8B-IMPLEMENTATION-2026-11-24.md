# PHASE 8B — vérifications finales

**Statut :** terminé localement

```text
python -m compileall -q app_base tests alembic  # OK
pytest -q                                       # 19 passed
ruff check .                                    # OK
alembic upgrade head --sql > $null              # OK
```

Les migrations PostgreSQL réelles, Redis réel, credentials S2S et appels
staging ne sont pas exécutés dans cet environnement.
