# S24-B — Journal

- L’ancien Compose local est conservé sous `docker-compose.local.yml`.
- `docker-compose.yml` contient désormais la stack staging avec les variables
  externes, S2S, webhooks, finance et OTEL.
- Le fichier redondant `docker-compose.portainer.yml` est supprimé.
- La stack Portainer existante peut donc continuer à utiliser son chemin Git
  `docker-compose.yml` après redéploiement.
- Le redéploiement Portainer reste à exécuter : l’audit live a confirmé que la
  stack actuellement démarrée utilise encore l’ancien Compose en mode
  développement.
