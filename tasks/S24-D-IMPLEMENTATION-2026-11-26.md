# S24-D — Journal d’implémentation

## A — Diagnostic

- La stack DiddiShop live est revenue en `staging` et l’API est saine.
- La map `DIDDI_SHOP_SERVICE_CLIENT_SECRETS` est présente et parsable dans le
  conteneur ; l’erreur Pydantic précédente venait donc d’une valeur Portainer
  mal encodée au moment du déploiement précédent.
- Le code DiddiSend staging audité protège encore les routes de livraison avec
  `X-Service-Key`/legacy et ne provisionne pas actuellement de client Shop.

## B — Correction locale

- DiddiShop demande maintenant `diddisend:deliveries:create` au lieu de
  `diddisend:deliveries:write`.
- Les tests et la documentation reflètent les quatre scopes attendus.
- Les variables explicites `DIDDISEND_CLIENT_ID`, `DIDDISEND_CLIENT_SECRET`,
  `DIDDISEND_AUDIENCE`, `DIDDISEND_ORIGIN_SERVICE` et
  `DIDDISEND_SERVICE_USER_ID` sont transmises par le Compose et prioritaires
  sur la map générique.
- Les appels sortants portent l’identité complète : Bearer, client, origine et
  UUID du sender technique.
- Le callback DiddiSend réel est normalisé depuis son enveloppe signée et
  dédupliqué par `event_id`.

## C — Configuration externe à appliquer

- Injecter dans DiddiShop le secret existant du client
  `diddishop-staging-diddisend` et l’UUID technique autorisé.
- Injecter dans DiddiSend l’URL callback
  `https://diddishop-backend.diddifree.com/internal/v1/webhooks/diddisend` et
  le même secret HMAC que `DIDDI_SHOP_DIDDISEND_WEBHOOK_SECRET`.
- Le credential DiddiFood ne doit pas être réutilisé.
- Une nouvelle recette E2E reste nécessaire après redéploiement ; aucun secret
  n’est écrit dans Git.

## D — Vérifications

- Vérifications à rejouer après la correction : tests ciblés, suite complète,
  Ruff, MkDocs strict, Compose staging/local et `git diff --check`.
