# Journal S3 — 2026-11-24

## Réalisé

- Alignement DiddiFiles sur l’OpenAPI staging observée.
- Validation locale du purpose et du statut des images catalogue.
- Injection de l’adaptateur DiddiFiles dans `CatalogService`.
- Ajout d’un port explicite pour les fichiers produit.
- Test de rejet d’un fichier qui n’est pas `diddishop_product_image`.

## Vérifications

- `31 passed`
- `ruff check .` OK
- compilation Python OK

## Déploiement en attente

- Confirmer avec DiddiFiles si les URLs produit doivent être publiques ou
  signées.
- Tester un upload réel avec un credential S2S DiddiShop.
