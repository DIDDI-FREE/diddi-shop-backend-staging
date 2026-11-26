# Portail documentaire public

Le portail MkDocs est un conteneur statique distinct dans la même stack Compose
que l’API. Il ne lit aucune
base, ne contient aucun secret et ne dépend pas de Git ou du poste du frontend
une fois publié.

## Construction locale

Le fichier Compose principal lance les quatre services, dont `docs` :

```powershell
docker compose up -d --build
Invoke-WebRequest http://localhost:48182/healthz
Invoke-WebRequest http://localhost:48182/
```

Le fichier `docker-compose.docs.yml` reste disponible pour un démarrage
documentation-only.

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

Comme dans DiddiGo, la stack Portainer dédiée
`docker-compose.portainer.yml` construit l’API et `Dockerfile.docs` depuis le
même checkout Git. Le conteneur `docs` fait donc partie de la même livraison
que l’API et sert le contrat correspondant à cette révision. Dans Portainer,
déployer ce fichier depuis le dépôt, puis définir au minimum :

```ini
DOCS_PUBLIC_ENABLED=true
DIDDI_SHOP_ENVIRONMENT=staging
DIDDI_SHOP_API_PORT=48180
DIDDI_SHOP_DOCS_PORT=48182
POSTGRES_PASSWORD=<secret hors Git>
DIDDI_SHOP_DATABASE_URL=postgresql+asyncpg://<user>:<password>@postgres:5432/<database>
```

Les URLs d’intégration, secrets S2S, credentials DiddiObserve et variables
OTEL sont également injectés dans l’environnement/secrets Portainer, jamais
dans le dépôt.

Le fichier prêt à charger dans Portainer est `portainer.env` (local, ignoré
par Git). Le modèle versionné est `portainer.env.example`. Remplacer toutes
les valeurs `REPLACE_WITH_*`, notamment le mot de passe PostgreSQL, les six
secrets clients DiddiFreeID, les secrets webhook et le Basic credential
DiddiObserve. Le mot de passe utilisé dans `DIDDI_SHOP_DATABASE_URL` doit être
URL-encodé s’il contient des caractères réservés.

La stack publie par défaut le port hôte `48182`, ce qui permet à Nginx Proxy
Manager de proxyfier sans réseau Docker partagé. Le port peut être remplacé
dans Portainer :

```ini
DIDDI_SHOP_DOCS_PORT=48282
```

Le Proxy Host API cible le même hôte Docker sur `DIDDI_SHOP_API_PORT` ; le
Proxy Host documentation cible `DIDDI_SHOP_DOCS_PORT`. Cette voie est le
fallback supporté quand le réseau Docker de Nginx Proxy Manager n’est pas
accessible depuis Portainer.

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

Avant le déploiement Portainer, valider le fichier comme Compose :

```powershell
docker compose -f docker-compose.portainer.yml config --quiet
```

Après le déploiement, vérifier dans Portainer que `diddishop-api-1` et
`diddishop-docs-1` sont `healthy`/`running`, puis configurer le Proxy Host NPM
vers le port docs choisi. Le domaine ne sera réellement prêt qu’après un
`200` HTTPS sur la racine et sur une page MkDocs.

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
