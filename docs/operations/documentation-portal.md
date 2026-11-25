# Portail documentaire public

Le portail MkDocs est un conteneur statique séparé de l’API. Il ne lit aucune
base, ne contient aucun secret et ne dépend pas de Git ou du poste du frontend
une fois publié.

## Construction locale

```powershell
docker compose -f docker-compose.docs.yml -f docker-compose.docs.local.yml up -d --build
Invoke-WebRequest http://localhost:18082/healthz
Invoke-WebRequest http://localhost:18082/
```

Le port local par défaut est `18082` et peut être changé avec `DOCS_PORT`.

Pour arrêter le portail local :

```powershell
docker compose -f docker-compose.docs.yml -f docker-compose.docs.local.yml down
```

## Publication staging

La stack staging doit construire `Dockerfile.docs` avec
`DOCS_PUBLIC_ENABLED=true` et publier le port hôte `18082` (ou un port libre).
Dans Nginx Proxy Manager, créer un Proxy Host :

```text
Domain: docs-diddishop-staging.diddifree.com
Forward scheme: http
Forward host: même hôte Docker que la stack DiddiShop
Forward port: 18082
Websockets: non requis
SSL: certificat staging pour docs-diddishop-staging.diddifree.com
```

Le frontend consommera alors uniquement :

```text
https://docs-diddishop-staging.diddifree.com/
```

Il ne doit pas charger Markdown depuis GitHub, le dépôt ou un ordinateur de
développement.

## Vérification après déploiement

```powershell
curl.exe -I https://docs-diddishop-staging.diddifree.com/
curl.exe -I https://docs-diddishop-staging.diddifree.com/api/API_CONTRACT/
```

Les deux réponses attendues sont `200`, avec un certificat TLS valide. Tant
que la première URL renvoie la page par défaut Nginx Proxy Manager ou qu’une
page retourne `404`, le Proxy Host n’est pas raccordé au conteneur docs.
