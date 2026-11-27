# Journal S24-X — 2026-11-27

## Constat

DiddiShop transmet désormais `origin_payment_reference`. DiddiSend valide le
trajet et le tarif, puis son `GET /payfund/v1/payment-intents/{id}` reçoit 404.
Le code DiddiPay audité refuse une intention dont `client_id` diffère du client
appelant. Le payload Shop ne contient pas de mécanisme de délégation.

## Implémentation

- Ajout de `DeliveryCreationUnavailableError` (`502`).
- Mapping des réponses non 2xx de `POST /v1/deliveries`, sans exposer le corps
  upstream ; seul le statut upstream est conservé dans `details`.
- Documentation DiddiPay/DiddiSend et décisions D-071/D-072.

## Vérifications

- `pytest -q tests/test_diddisend_runtime_contract.py tests/test_payment_delivery_flow.py` : 14 passed.
- `ruff check app_base/core/errors.py app_base/integrations/diddisend.py tests/test_diddisend_runtime_contract.py` : OK.
- Vérification staging en attente d’un contrat Pay/Send et d’un rejeu manuel.
