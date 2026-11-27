# S24-I — normalisation du devis DiddiSend

## Diagnostic

Grafana a confirmé deux variantes d’échec : DiddiSend pouvait répondre 502
après une route DiddiMap avec des métriques nulles, ou répondre avec `quote`
comme objet. DiddiShop tentait alors `int(dict)`.

## Implémentation

- Normalisation des montants numériques et structurés.
- Rejet explicite des réponses sans montant valide.
- Mapping des erreurs HTTP DiddiSend en `502 DELIVERY_QUOTE_UNAVAILABLE`.
- Tests des formats numériques, objet et erreur upstream.

## Vérifications

- `pytest -q` : 87 tests passés.
- `ruff check .` : OK.
- `git diff --check` : OK.

## Déploiement

Aucun déploiement Portainer n’est effectué par Codex. La recette doit vérifier
le devis avec un trajet non nul après déploiement manuel.
