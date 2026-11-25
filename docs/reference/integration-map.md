# Carte des intégrations

Cette carte résume les frontières d’intégration. La version de conception
complète reste dans le fichier `INTEGRATION_MAP.md` à la racine du dépôt.

```text
checkout/orders ──> DiddiPay       PaymentIntent / refund / webhooks
                 └─> DiddiSend     quote / delivery / tracking
catalog          ──> DiddiFiles    upload / metadata / URLs
checkout/rewards ──> DiddiRewards  quote / reserve / confirm / correct
claims/support   ──> DiddiSupport  context / cases
tasks métier     ──> DiddiComms    conversation uniquement
tous processus   ──> DiddiObserve  OTLP logs / traces / metrics
identité/S2S     ──> DiddiFreeID   JWT / client_credentials
opérations       ──> DiddiBackoffice API DiddiShop, jamais DB directe
```

DiddiMap et un service de flotte ne font pas partie de cette carte. DiddiSend
est l’unique propriétaire de l’expédition.
