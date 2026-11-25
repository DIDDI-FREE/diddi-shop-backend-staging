# Journal S14 — 2026-11-25

## Livré

- `Dockerfile.docs` : build MkDocs strict puis image Nginx statique ;
- `docker-compose.docs.yml` et `docker-compose.docs.local.yml` ;
- configuration Nginx activée/masquée par `DOCS_PUBLIC_ENABLED` ;
- absence de binding hôte dans le Compose de staging et overlay réseau
  `NPM_NETWORK` pour Nginx Proxy Manager ;
- guide de publication avec Proxy Host attendu pour
  `docs-diddishop-staging.diddifree.com` ;
- exclusion des artefacts MkDocs du suivi Git.

## Vérifications

- `mkdocs build --strict` : OK ;
- `docker compose ... config --quiet` : OK ;
- build Docker du portail : OK ;
- `http://localhost:18082/healthz` : 200 ;
- `http://localhost:18082/` : 200, titre DiddiShop Documentation ;
- `http://localhost:18082/api/API_CONTRACT/` : 200 ;
- conteneur docs : `healthy`.

## Vérification externe

Le domaine staging actuel n’est pas encore raccordé au portail :

- HTTP renvoie la page par défaut Nginx Proxy Manager ;
- HTTPS échoue sur la connexion TLS ;
- les pages documentaires publiques ne sont donc pas encore disponibles.

Le raccordement DNS/Proxy Host/certificat doit être réalisé côté
infrastructure. Il ne faut pas déclarer l’URL frontend prête avant une réponse
HTTPS 200 sur la racine et sur une page documentaire.

Le réseau NPM n’existe pas sur le poste local inspecté ; son nom doit être
fourni par l’hôte où Nginx Proxy Manager est déployé.
