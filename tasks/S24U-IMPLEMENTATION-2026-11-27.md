# S24-U — Journal d’implémentation

## Résultat

- Les coordonnées `dropoff_latitude` et `dropoff_longitude` sont exposées dans
  `OrderResponse` depuis `delivery_request.dropoff_location`.
- `DeliveryProjection` et `DeliveryResponse` portent `eta_minutes`.
- La valeur est acceptée depuis `eta_minutes` ou
  `estimated_duration_minutes` quand DiddiSend l’envoie ; sinon elle reste
  `null`.
- La documentation API et DiddiSend précise la source de vérité et interdit
  une ETA locale inventée.

## Vérifications

- `python -m pytest -q` : 239 passed.
- `python -m mkdocs build --strict --site-dir .mkdocs-build-check` : OK.
- `git diff --check` : OK.
- Ruff présente deux erreurs préexistantes hors de ce lot : une règle sur le
  parsing ISO déjà présent et un import désordonné dans
  `tests/test_contract_wiring.py`.

## Déploiement

Aucun déploiement ni redéploiement Portainer. Vérification staging laissée à
l’utilisateur : coordonnées dans les commandes et ETA réellement envoyée par
DiddiSend.
