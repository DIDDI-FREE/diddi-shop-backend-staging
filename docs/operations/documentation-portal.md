# Portail documentaire public

Le portail MkDocs est un conteneur statique séparé de l’API. Il ne lit aucune
base, ne contient aucun secret et ne dépend pas de Git ou du poste du frontend
une fois publié.

## Construction locale

```powershell
docker compose -f docker-compose.docs.yml up -d --build
Invoke-WebRequest http://localhost:48182/healthz
Invoke-WebRequest http://localhost:48182/
```

Le port hôte par défaut est `48182` et peut être changé avec
`DIDDI_SHOP_DOCS_PORT`.

Pour arrêter le portail local :

```powershell
docker compose -f docker-compose.docs.yml down
```

## Publication staging

La stack staging doit construire `Dockerfile.docs` avec
`DOCS_PUBLIC_ENABLED=true`. Par défaut, elle publie le port hôte `48182`, ce
qui permet à Nginx Proxy Manager de proxyfier sans réseau Docker partagé.
Le port peut être remplacé dans Portainer :

```ini
DIDDI_SHOP_DOCS_PORT=48282
```

Si le réseau Docker NPM est accessible, l’overlay réseau reste disponible :

```powershell
$env:NPM_NETWORK = "<nom-exact-du-reseau-partage-avec-NPM>"
docker compose -f docker-compose.yml -f docker-compose.docs.yml -f docker-compose.proxy.yml up -d --build
```

Dans Nginx Proxy Manager, créer un Proxy Host :

```text
Domain: docs-diddishop-staging.diddifree.com
Forward scheme: http
Forward host: même hôte Docker que la stack DiddiShop
Forward port: 48182
Websockets: non requis
SSL: certificat staging pour docs-diddishop-staging.diddifree.com
```

Le Proxy Host API utilise le host Docker et le port `48180`. Le Proxy Host
documentation utilise le host Docker et le port `48182`. Avec l’overlay réseau,
les cibles deviennent `api:8000` et `docs:80`.

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
