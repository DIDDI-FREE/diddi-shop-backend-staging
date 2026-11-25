# Intégration DiddiSupport

DiddiSupport est propriétaire des dossiers, décisions opérateur et règles de
support. DiddiShop fournit un contexte métier sans donner un accès direct à
ses tables.

## Parcours

- `GET /support/v1/internal/context/{origin_service}/{resource_type}/{resource_id}`
  pour enrichir le contexte d’une commande ou d’une réclamation ;
- `POST /support/v1/internal/cases` pour créer ou retrouver un cas idempotent.

La route de contexte doit rester en lecture et la création de cas doit porter
une clé stable, l’acteur et la référence métier. L’enveloppe exacte, les
scopes et les statuts de cas sont encore à confirmer en staging.
