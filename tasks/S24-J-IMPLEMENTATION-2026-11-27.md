# S24-J — Alignement PaymentIntent DiddiPay

## Diagnostic

Le schéma OpenAPI staging de DiddiPay accepte `channel` et `network`, avec
`network` limité à `orange`, `wave` et `mtn`. Il rejette les propriétés
supplémentaires. L’adaptateur Shop envoyait encore `payment_method` et
`return_url`, ce qui explique le HTTP 422 avec `wave`.

## Implémentation

- `wave` → `channel=mobile_money`, `network=wave`.
- `mtn_momo` → `channel=mobile_money`, `network=mtn`.
- `orange_money` → `channel=mobile_money`, `network=orange`.
- Suppression de `payment_method` et `return_url` du payload DiddiPay.
- Conservation de la validation Shop : `cash` reste refusé.

## Vérifications

- `pytest -q`.
- `ruff check .`.
- Déploiement Portainer : manuel par l’utilisateur uniquement.
