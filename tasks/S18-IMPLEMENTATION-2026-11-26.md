# S18 — journal d’implémentation

## S18-A/B — réponses et catégories

- Ajout des modèles Pydantic de réponse dans `app_base/core/api_contracts.py`.
- Ajout de `GET /v1/catalog/categories`.
- Déclaration des `response_model` sur les routes frontend principales.
- Documentation des champs boutique, des enveloppes de listes et des états
  produit.

## S18-C — médias DiddiFiles

- La session d’upload utilise `module_owner`, `purpose`, `filename`,
  `mime_type`, `size_bytes` et `metadata` conformément au staging DiddiFiles.
- DiddiShop appelle `confirm` avant de rattacher le fichier au produit.
- Les listes de produits calculent `photo_urls` depuis les métadonnées publiques
  retournées par DiddiFiles.

## S18-D — vérification

- `ruff check .` : OK.
- `pytest -q` : 63 tests passés.
- `python -m compileall -q app_base` : OK.
- `git diff --check` : OK.
- `mkdocs build --strict` : OK.
- images Docker `api` et `docs` : construites avec succès.

## Déploiement en attente

- Redéployer la stack Portainer pour publier l’OpenAPI et MkDocs mis à jour.
- Vérifier les routes et la documentation sur les domaines publics.
