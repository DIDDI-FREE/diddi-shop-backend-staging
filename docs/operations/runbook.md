# Runbook DiddiShop MVP

## Incident paiement

1. Lire la commande via `/v1/admin/shop/orders/{order_id}`.
2. Comparer l’état local avec DiddiPay à partir de `payment_intent_id`.
3. Ne jamais créer une nouvelle clé lorsqu’une opération est inconnue.
4. Rejouer avec la même clé après vérification de l’état externe.

## Incident livraison

1. DiddiSend est la source de vérité de la livraison.
2. Lire la projection locale et la référence `delivery_id`.
3. Rejouer avec `shop:create-delivery:{order_id}:1` uniquement après contrôle.
4. Ne jamais appeler un service de flotte ou DiddiMap depuis DiddiShop.

## Outbox et inbox

- une outbox bloquée est réessayée avec backoff ;
- une inbox déjà traitée retourne un résultat idempotent ;
- même `consumer + event_id` avec payload différent est un incident de contrat.

## Déploiement staging

Avant recette : migrations Alembic, PostgreSQL, Redis, clients et scopes S2S,
secrets webhook, URLs HTTPS, DiddiObserve OTLP et test des endpoints
`/health`/`/ready`. La recette financière utilise uniquement des scénarios
autorisés et sans transaction réelle non approuvée.
