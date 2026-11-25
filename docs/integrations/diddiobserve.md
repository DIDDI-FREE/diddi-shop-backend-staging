# Intégration DiddiObserve

DiddiObserve reçoit la télémétrie, mais ne possède aucune règle de commande.
DiddiShop utilise OpenTelemetry en OTLP HTTP/protobuf.

## Configuration

```ini
OTEL_SERVICE_NAME=diddishop
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=https://logs-otel.diddifree.com/otlp/diddishop/v1/logs
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://logs-otel.diddifree.com/otlp/diddishop/v1/traces
```

Le header Authorization est un credential Basic dédié, injecté hors Git. Aucun
client ou scope métier DiddiFreeID n’est réutilisé.

## Données et corrélation

Les ressources exposent `service.name=diddishop`, namespace `diddi`, version,
instance, environnement, déploiement et `diddi.component` (`api`, `worker` ou
`scheduler`). `traceparent` est propagé ; `request_id` et `correlation_id`
servent à la recherche mais ne remplacent pas `trace_id`/`span_id`.

Les secrets, tokens, cookies, headers d’authentification, données de paiement,
corps complets, téléphones, emails, adresses et IP complètes sont filtrés par
défaut. L’export est asynchrone, borné, limité à 64 KiB par événement et 4 MiB
par requête, avec retries réseau/429/502/503/504.

La panne du collecteur ne doit jamais bloquer une commande ; les pertes et
rejets sont comptés. Le scrape Prometheus et les marqueurs API/worker restent
à vérifier sur le déploiement staging.
