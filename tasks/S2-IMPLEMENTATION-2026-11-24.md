# Journal S2 — 2026-11-24

## Réalisé

- `JwtVerifier` avec cache JWKS, audience, issuer et expiration obligatoires.
- `current_actor` accepte le header de test uniquement en développement.
- Les scopes des clients S2S sont dérivés du service appelé.
- Les webhooks DiddiPay et DiddiSend vérifient une signature HMAC hors local.
- Les secrets webhook restent externes au dépôt.

## Vérifications

- `28 passed`
- `ruff check .` OK
- compilation Python OK

## Déploiement en attente

- Configurer issuer/audience et JWKS DiddiFreeID.
- Provisionner un credential et les scopes pour chaque service.
- Configurer les secrets de callbacks DiddiPay/DiddiSend.
