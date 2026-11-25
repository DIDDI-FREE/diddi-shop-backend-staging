# Référence de configuration

**Source :** `app_base/core/settings.py` et `.env.example`.

Les valeurs sensibles sont injectées par le secret manager ou Compose hors
Git. Les exemples ci-dessous décrivent des noms de variables, pas des secrets.

## Groupes

| Groupe | Variables principales | Finalité |
| --- | --- | --- |
| Runtime | `DIDDI_SHOP_ENVIRONMENT`, `DIDDI_SHOP_APP_NAME` | environnement et identité |
| Données | `DIDDI_SHOP_DATABASE_URL`, `DIDDI_SHOP_REDIS_URL` | PostgreSQL et Redis |
| DiddiFreeID | `DIDDI_SHOP_DIDDIFREEID_*` | JWKS et token service |
| Cibles S2S | `DIDDI_SHOP_SERVICE_CLIENT_IDS`, `DIDDI_SHOP_SERVICE_CLIENT_SECRETS` | un client par service |
| Intégrations | `DIDDI_SHOP_DIDDIPAY_BASE_URL`, `DIDDI_SHOP_DIDDISEND_BASE_URL`, etc. | bases HTTPS |
| Webhooks | `DIDDI_SHOP_DIDDIPAY_WEBHOOK_SECRET`, `DIDDI_SHOP_DIDDISEND_WEBHOOK_SECRET` | signatures entrantes |
| V1 finance | `DIDDI_SHOP_SELLER_RELEASE_ENABLED=false` | interdit la release V1 |
| DiddiObserve | `OTEL_*`, `DEPLOYMENT_ID`, `DIDDI_COMPONENT` | OTLP et ressource telemetry |

## Clients S2S

`SERVICE_CLIENT_IDS` et `SERVICE_CLIENT_SECRETS` sont des maps JSON. Chaque
cible possède son propre client : `diddipay`, `diddisend`, `diddifiles`,
`diddirewards`, `diddicomms` et `diddisupport`. Il n’existe pas de fallback
staging vers `service_client_id` unique.

Les tokens sont demandés avec `client_credentials`, audience de la cible et
scopes dédiés. Le token court est mis en cache jusqu’à expiration ; les
secrets ne sont jamais consignés.

## Sécurité d’environnement

En environnement non développement, l’application refuse :

- une base externe absente ou non HTTPS ;
- un client ou secret S2S manquant ;
- un endpoint OTLP ou credential manquant lorsque les logs sont activés.

Le Compose local est explicitement en `development` et utilise des valeurs
locales non sensibles.

## DiddiObserve

Le transport est OTLP HTTP/protobuf. Les endpoints complets se terminent par
`/v1/logs` et `/v1/traces`. Le header `OTEL_EXPORTER_OTLP_HEADERS` contient
uniquement le credential Basic dédié à l’observabilité ; il ne faut pas y
mettre un token métier ou un client DiddiFreeID.
