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

## Diagnostic complémentaire

Le conteneur Portainer actuel contient bien le code S24-F et les variables
issuer/audience attendues. Ses logs montrent uniquement `401`, car le détail
de l’exception PyJWT était masqué. Un journal sûr a été ajouté : il conserve
le type et le message de rejet, jamais le JWT.

Après contrôle, le logger initial était routé vers l’export OTLP et n’était
donc pas visible dans `docker logs`. Le diagnostic sûr est maintenant envoyé
aux deux sorties (`diddi_shop.auth` pour DiddiObserve et `uvicorn.error` pour
Docker), sans journaliser le token. Il faut redéployer cette version, puis
effectuer un appel réel avec un JWT acheteur pour obtenir la cause PyJWT
exacte. Le contrôle Portainer du 27/11/2026 confirme que le conteneur est
healthy, mais aucun appel réel postérieur au redéploiement n’a encore fourni
ce diagnostic.
