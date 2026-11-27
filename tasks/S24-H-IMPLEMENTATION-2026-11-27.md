# S24-H — réhydratation du statut produit

## Diagnostic

Le payload JSON PostgreSQL stockait `status` comme texte. Le repository
reconstruisait directement `Product`, puis le panier appelait
`product.status.value`, ce qui provoquait HTTP 500.

## Implémentation

- Ajout d’un helper de repository qui convertit le statut en `ProductStatus`.
- Application à `get`, `list_published`, `list_for_shop` et `apply_stock`.
- Ajout d’un test de round-trip SQL du statut enum.

## Vérifications

- `pytest -q` : 83 tests passés.
- `ruff check .` : OK.
- `git diff --check` : OK.

## Déploiement

Aucun déploiement Portainer n’est effectué par Codex. La recette staging doit
rejouer l’ajout au panier et le devis après déploiement manuel.
