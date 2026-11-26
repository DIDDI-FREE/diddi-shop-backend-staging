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

## C — Blocage externe restant

- DiddiSend doit accepter les tokens JWT S2S DiddiFreeID avec audience
  `diddisend`, ou fournir à DiddiShop un service-key dédié et un identifiant
  technique UUID.
- Le credential DiddiFood ne doit pas être réutilisé.

## D — Vérifications

- Tests ciblés : 7 passés ;
- Suite complète : 74 tests passés, 1 avertissement de dépréciation
  Starlette/httpx existant dans l’environnement ;
- Ruff : OK ;
- MkDocs strict : OK ;
- Compose staging et local : OK ;
- `git diff --check` : OK.
