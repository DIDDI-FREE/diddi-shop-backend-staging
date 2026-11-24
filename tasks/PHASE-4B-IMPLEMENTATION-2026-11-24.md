# PHASE 4B — vérification

**Statut :** terminé

```text
python -m compileall -q app_base tests alembic
pytest -q
9 passed
```

Le quote et le paiement réels restent remplaçables par faux ports dans les
tests et sont dépendants des credentials S2S en environnement réel.
