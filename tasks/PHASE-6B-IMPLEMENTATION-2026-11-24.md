# PHASE 6B — décisions et vérification

**Statut :** terminé

Les décisions acheteur/vendeur/partielle sont auditables par l’agrégat Claim.
La release n’est demandée qu’après la fenêtre de 72 heures et reste derrière
le port DiddiPay non confirmé.

```text
python -m compileall -q app_base tests alembic
pytest -q
14 passed
```
