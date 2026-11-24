# Journal S7 — 2026-11-24

## Réalisé

- Cycle complet de bénéfice Rewards derrière l’adaptateur.
- Alignement DiddiComms sur la route staging de conversation par tâche, sans
  payload JSON ni prétention d’envoi de notification.
- Alignement DiddiSupport sur la route interne `/support/v1/internal/cases`.
- Ouverture de cas support depuis un contexte DiddiShop sans accès direct aux
  tables externes.
- Scopes Comms/Support spécifiques à DiddiShop.
- Export Observe conservé comme port configurable, car l’endpoint OTLP répond
  actuellement `502`.

## Vérifications

- `37 passed`
- `ruff check .` OK
- compilation Python OK

## Déploiement en attente

- Confirmer le couple owner/type de tâche et l’autorisation S2S DiddiComms.
- Configurer les scopes Rewards/Comms/Support réels.
- Rétablir et tester l’ingestion DiddiObserve.
