# S24-E — Journal d’implémentation

## Diagnostic

- Portainer et la stack DiddiShop sont joignables ; les variables DiddiSend
  sont présentes.
- Le `401` est émis par `POST /v1/checkouts/quote` avant l’appel DiddiSend.
- La vérification JWKS plante sur `jwt.algorithms.RSAAlgorithm`.

## Correction

- Remplacement par `PyJWK.from_dict(item).key`.
- Désinstallation préventive du package générique `jwt` dans le Dockerfile.
- Contrôle de build : PyJWT v2 et `PyJWK` doivent être importables.
- Test de régression ajouté.

## Vérifications

- Suite : 79 tests passés ;
- Ruff : OK ;
- Build Docker local sans cache : OK.

## Déploiement en attente

- Reconstruire et redéployer l’image API depuis ce commit dans Portainer.
- Rejouer `GET /v1/cart` puis `POST /v1/checkouts/quote` avec le JWT acheteur.
