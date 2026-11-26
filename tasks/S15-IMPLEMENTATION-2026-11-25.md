# Journal S15 — 2026-11-25

## S15-A/B — Stack Portainer et documentation

- Ajout de `docker-compose.portainer.yml`, inspiré du modèle DiddiGo.
- L’API et le conteneur MkDocs sont dans la même stack et utilisent le même
  checkout Git/build context.
- `DOCS_PUBLIC_ENABLED` est désactivé par défaut ; Portainer staging doit le
  définir explicitement à `true`.
- Les ports hôte API/docs restent configurables pour le raccordement NPM sans
  réseau Docker partagé.
- Documentation ajoutée pour les variables Portainer et les Proxy Hosts NPM.
- Ajout de `portainer.env` local, prêt à charger après remplacement des
  secrets, et de `portainer.env.example` versionné avec les valeurs staging
  non sensibles.
- Le service `docs` est également présent dans `docker-compose.yml`, afin que
  la stack Compose principale utilisée par Portainer ne puisse pas oublier
  MkDocs.

## S15-C — Vérifications

- `docker compose -f docker-compose.portainer.yml config --quiet` : à exécuter.
- `mkdocs build --strict` : à exécuter.
- `docker compose -f docker-compose.portainer.yml build docs` : à exécuter.
- Déploiement Portainer/NPM : en attente d’accès infrastructure.
