# DiddiShop — runbook MVP

## Incident paiement

1. Lire la commande via `/v1/admin/shop/orders/{order_id}`.
2. Comparer le statut local avec DiddiPay à partir de `payment_intent_id`.
3. Ne jamais rejouer une opération avec une nouvelle clé si l’issue de la
   précédente est inconnue.
4. Rejouer avec la même clé après confirmation de l’opération initiale.

## Incident livraison

1. DiddiSend est la source de vérité de la livraison.
2. Lire la projection locale et interroger DiddiSend avec `delivery_id`.
3. Rejouer la demande avec `shop:create-delivery:{order_id}:1`.
4. Ne jamais appeler un service de flotte depuis DiddiShop.

## Outbox/inbox

- Une outbox bloquée est réessayée avec backoff.
- Une inbox déjà traitée retourne un succès idempotent.
- Un payload différent pour le même `consumer + event_id` est un incident de contrat.

## Déploiement

Avant staging : migrations Alembic, PostgreSQL, Redis, clients S2S, signatures
webhook, URLs DiddiPay/DiddiSend/DiddiFiles/DiddiRewards/DiddiComms/
DiddiSupport/DiddiObserve.
