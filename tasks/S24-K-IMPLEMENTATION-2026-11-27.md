# S24-K — Échec PaymentIntent et retry checkout

## Diagnostic

DiddiPay retournait correctement `status=failed`, mais DiddiShop construisait
toujours le checkout avec son statut par défaut `payment_pending`. La route de
retry refusait donc le checkout avec HTTP 409.

## Implémentation

- Mapping des statuts fournisseur vers `payment_pending`, `payment_succeeded` ou
  `payment_failed`.
- Persistance de `payment_failure_code`, `payment_failure_message` et
  `payment_provider_status`.
- Retry avec nouvelle clé : transition persistée vers pending avant l'appel,
  puis résultat final persisté.
- Les champs de diagnostic sont exposés dans la réponse Payment du checkout.

## Vérifications

- `pytest -q` : 88 passed.
- `ruff check .` : OK.
- Déploiement Portainer : manuel par l'utilisateur uniquement.
