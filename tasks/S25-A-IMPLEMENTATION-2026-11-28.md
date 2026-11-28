# S25-A — Journal d’implémentation

## Réalisé

- Ajout d’un noyau monétaire XOF basé sur `Decimal`.
- Normalisation `ROUND_CEILING` pour prix, frais, paiements,
  remboursements, remises, récompenses, devis et payouts.
- Normalisation `ROUND_FLOOR` pour les soldes disponibles.
- Application aux contrats Pydantic, catalogues, checkout, commandes,
  finance, webhooks, DiddiPay, DiddiSend et DiddiRewards.
- Normalisation à la lecture des payloads JSON historiques, sans migration ni
  réécriture de la base.
- Tests dédiés ajoutés dans `tests/test_money_rounding.py`.

## Vérifications

- `pytest -q tests/test_money_rounding.py`
- `pytest -q`
- `ruff check .`
- `python -m compileall -q app_base tests alembic`
- `mkdocs build --strict`

## Déploiement en attente

Déploiement manuel depuis GitHub par l’utilisateur. Aucun accès Portainer ni
déploiement n’a été effectué par l’agent.
