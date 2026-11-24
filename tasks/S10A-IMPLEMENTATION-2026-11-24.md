# S10-A — Contrat DiddiComms conversation

## Réalisé

- remplacement de `create_task(payload)` par `open_conversation(...)` ;
- suppression du body JSON sur `/comms/v1/tasks/.../conversation` ;
- validation UUID de `task_id` et encodage des segments URL ;
- adaptation du port et du service de communication ;
- retrait de la prétendue notification événementielle ;
- scope Comms laissé vide tant qu’aucun scope S2S n’est publié par l’OpenAPI.

## Vérifications

- `pytest -q` : 43 passed ;
- `ruff check .` : OK ;
- `python -m compileall -q app_base tests alembic` : OK ;
- `git diff --check` : OK.

## Déploiement en attente

Confirmer avec DiddiComms le couple owner/type de tâche, l’autorisation S2S et
le futur contrat séparé pour les notifications déclenchées par événements.
