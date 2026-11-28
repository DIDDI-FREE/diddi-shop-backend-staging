# Intégration DiddiSupport

DiddiSupport est propriétaire des dossiers, décisions opérateur et règles de
support. DiddiShop fournit un contexte métier sans donner un accès direct à
ses tables.

## Parcours

- `GET /support/v1/internal/context/{origin_service}/{resource_type}/{resource_id}`
  pour enrichir le contexte d’une commande ou d’une réclamation ;
- `POST /support/v1/internal/cases` pour créer ou retrouver un cas idempotent.

La route de contexte exposée par DiddiShop est disponible sous les deux chemins
suivants pour compatibilité avec les clients existants :

- `GET /internal/v1/support/orders/{order_id}/context` ;
- `GET /internal/v1/support/order/{order_id}/context` (alias de compatibilité,
  non publié séparément dans OpenAPI).

Les deux routes renvoient l’enveloppe standard `diddi.context.v1` :

```json
{
  "protocol": "diddi.context.v1",
  "origin_service": "diddishop",
  "resource_type": "order",
  "resource_id": "uuid",
  "data": {
    "order": {},
    "delivery": null,
    "claim": null,
    "owner_service": "diddishop",
    "source_of_truth": {}
  },
  "redacted_fields": [],
  "as_of": "2026-01-01T00:00:00Z",
  "fetched_at": "2026-01-01T00:00:00Z"
}
```

`as_of` et `fetched_at` sont des timestamps UTC ISO 8601. `data` contient le
contexte métier et `redacted_fields` liste les champs volontairement masqués.
La route reste en lecture ; la création de cas porte une clé stable, l’acteur
et la référence métier.
