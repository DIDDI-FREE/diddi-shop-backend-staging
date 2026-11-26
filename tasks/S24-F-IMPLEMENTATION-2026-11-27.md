# S24-F — Journal d’implémentation

## Diagnostic

Le JWT acheteur staging contient `iss=diddifree-id`, `sub` et `exp`, mais pas
de claim `aud`. DiddiShop envoyait pourtant `audience=diddishop` à PyJWT.
Le Compose utilisait en plus `:-diddishop`, donc une audience vide était
remplacée par `diddishop`. L’issuer vide désactivait silencieusement sa propre
vérification.

## Implémentation

- Les routes frontend vérifient signature, `exp`, `sub` et issuer sans exiger
  `aud`.
- Les routes internes S2S vérifient explicitement `aud=diddishop`.
- L’issuer staging est obligatoire et documenté comme `diddifree-id`.
- Ajout de tests pour les deux comportements.

## Vérifications

- `pytest -q` : 81 tests passés ;
- `ruff check .` : OK.

## Déploiement en attente

- Ajouter `DIDDI_SHOP_DIDDIFREEID_ISSUER=diddifree-id` dans Portainer ;
- reconstruire et redéployer l’image API ;
- rejouer le panier et les commandes avec le même JWT acheteur.
