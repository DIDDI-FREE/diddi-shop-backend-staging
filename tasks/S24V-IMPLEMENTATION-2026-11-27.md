# S24-V — Journal d’implémentation

## Diagnostic

La stack `diddishop-backend` staging était saine : API, PostgreSQL, Redis et
documentation healthy. Les coordonnées sender étaient présentes dans la
configuration runtime et la stack pointait sur le commit GitHub déployé.
Le défaut concernait les snapshots de commandes historiques, créés avant que
les coordonnées sender deviennent obligatoires.

## Correction

`DeliveryService.request_for_order` réinjecte `sender_phone` et
`sender_email` au bord de l’intégration. L’email est dérivé du téléphone si
aucun email configuré n’est disponible. La création reste idempotente.

## Vérifications

- Tests ciblés : 12 passed.
- Suite complète et rejeu staging : à confirmer après déploiement manuel.
- Aucun déploiement ou redéploiement Portainer effectué par l’agent.
