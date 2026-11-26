# Journal S16 — 2026-11-26

## Livré

- Catalogue publié listable avec recherche texte et catégorie.
- Produits publics d’une boutique et espaces vendeur (`/mine`, `my-products`).
- Modification vendeur du titre, prix, stock et catégorie.
- Suppression complète d’une ligne panier.
- Listes commandes acheteur et commandes vendeur à confirmer.
- Session d’upload DiddiFiles et attachement d’une photo confirmée.
- Réponse checkout avec paiement DiddiPay normalisé sans tokens/secrets.
- Codes d’erreur `NOT_FOUND`, `CONFLICT`, `VALIDATION_ERROR`, etc.
- Documentation API, MVP, DiddiFiles et tests de contrat frontend.

## Vérifications

- `ruff check .` : OK.
- `pytest -q` : 58 passed.
- `python -m compileall -q app_base tests alembic` : OK.
- `git diff --check` : OK.
