# Intégration DiddiFreeID

DiddiFreeID fournit l’identité humaine, les clés JWKS et les credentials de
service. DiddiShop ne partage pas un client S2S unique entre intégrations.

## Utilisateur

En environnement non développement, les routes protégées valident un JWT
Bearer avec `exp`, `sub`, audience et, si configuré, issuer. Les rôles sont
convertis en contexte `user`, `support`, `admin` ou `service`.

## Service à service

Chaque cible dispose d’un client `client_credentials` propre :

```text
diddishop -> client diddipay  -> audience diddipay  -> scopes DiddiPay
diddishop -> client diddisend -> audience diddisend -> scopes DiddiSend
diddishop -> client diddifiles -> audience diddifiles -> scopes Files
...
```

Le token court est mis en cache par cible. `X-Client-ID` doit correspondre au
client utilisé. Une absence de client ou de secret fait échouer le démarrage
non développement.

## Sécurité

Les secrets restent hors dépôt. Un client d’une cible ne doit pas être utilisé
pour appeler une autre cible et aucun secret S2S ne doit être transmis à un
client frontend.
