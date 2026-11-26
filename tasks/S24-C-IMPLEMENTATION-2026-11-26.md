# S24-C — Journal d’implémentation

## A — Secret et signature

- Le champ `diddipay_webhook_secret` existait déjà dans `Settings` et est lu
  sous le nom `DIDDI_SHOP_DIDDIPAY_WEBHOOK_SECRET`.
- Le vérificateur accepte désormais un nom d’en-tête et un timestamp optionnel.
- DiddiPay utilise `X-DiddiPay-Signature` et aucun timestamp.

## B — Enveloppe fournisseur

- Ajout du modèle `DiddiPayCallbackEnvelope`.
- Le routeur lit le corps brut après vérification, puis adapte
  `{id, type, occurred_at, data}` vers `ExternalEvent`.
- L’ancien format interne reste accepté pour compatibilité.

## C — Rattachement métier

- `data.checkout_id` est prioritaire.
- Sinon `data.business_reference` au format
  `diddishop:checkout:{checkout_id}` est converti en `checkout_id`.
- Un callback DiddiPay non rattachable à un checkout ou une commande est
  rejeté en `422` au lieu d’être marqué traité silencieusement.

## D — Vérifications

- `python -m pytest -q` : 74 tests passés, 1 avertissement de dépréciation
  Starlette/httpx existant dans l’environnement ;
- `ruff check app_base tests` : OK ;
- `mkdocs build --strict` : OK ;
- `git diff --check` : OK ;
- `docker compose ... config --quiet` pour staging et local : OK.
