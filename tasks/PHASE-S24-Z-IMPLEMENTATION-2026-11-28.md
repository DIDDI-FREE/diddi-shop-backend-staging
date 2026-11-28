# S24-Z — implémentation

## Réalisé

- Ajout de `GET /internal/v1/support/order/{order_id}/context` comme alias de
  compatibilité de la route plurielle.
- Normalisation de la réponse vers `diddi.context.v1` avec `data`,
  `redacted_fields`, `as_of` et `fetched_at`.
- Mise à jour des contrats MkDocs et du suivi de déploiement.
- Ajout d’un test de forme d’enveloppe.

## Vérifications

- `pytest -q` : 245 passed.
- `ruff check` sur les fichiers modifiés : passed.
- `docker compose -f docker-compose.yml --env-file portainer.env config --quiet` : passed
  avec valeurs temporaires uniquement pour les deux champs sender absents du
  fichier local ; aucune valeur secrète n’a été modifiée.
- `mkdocs build --strict` : passed.

## Déploiement restant

Déploiement manuel par l’utilisateur depuis GitHub, puis rejeu du test
DiddiSupport. Aucun accès en écriture Portainer n’a été utilisé.

