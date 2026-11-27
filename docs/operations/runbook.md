# Runbook DiddiShop MVP

## Incident paiement

1. Lire la commande via `/v1/admin/shop/orders/{order_id}`.
2. Comparer l’état local avec DiddiPay à partir de `payment_intent_id`.
3. Ne jamais créer une nouvelle clé lorsqu’une opération est inconnue.
4. Rejouer avec la même clé après vérification de l’état externe.

### Paiement réussi chez DiddiPay mais webhook Shop en 500

Ne pas lancer `/v1/checkouts/{id}/retry` et ne pas recréer un paiement pour
réparer une notification. La réussite d'un écran sandbox ne suffit pas : faire
confirmer l'intention et son événement `payment.succeeded` par DiddiPay.

1. L'utilisateur déploie manuellement le correctif depuis GitHub. Aucun agent
   ne déploie ni ne redéploie sur Portainer.
2. Laisser DiddiPay réessayer le callback ; si ses reprises sont épuisées,
   demander à son équipe de rejouer **la notification originale** pour le même
   PaymentIntent, avec sa signature HMAC et son `event_id` d'origine. Ne pas
   fabriquer un événement de succès et ne pas changer les états en base.
3. Attendre `POST /internal/v1/webhooks/diddipay → 200 processed`. Un événement
   déjà acquitté retourne `200 duplicate`. Une sauvegarde échouée ne marque pas
   l'événement comme traité dans l'inbox.
4. Vérifier `GET /v1/checkouts/{id}` : `status=payment_succeeded` ; commande :
   `fulfillment_status=TO_CONFIRM` et `payment_status=HELD` (nom historique de
   la projection locale, **pas** une séquestration V1). Le vendeur doit voir la
   commande via `/v1/orders/seller/to-confirm`.
5. Vérifier confirmation vendeur, `ready`, création DiddiSend et lecture du
   suivi. Un rejeu de `ready` doit réutiliser la livraison existante.

Incident du 27 novembre : les enums de commande/boutique/livraison restaient
des chaînes après JSON, et la transition rechargeait la commande en perdant
la mise à jour paiement/Rewards. Correction S24-P sans migration ni nouvelle
variable d'environnement. Le mapping des états publics reste inchangé.

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

### Migrations de démarrage

Le service `api` exécute automatiquement `alembic upgrade head` avant Uvicorn
dans le Compose staging. Cette étape est obligatoire pour les volumes
PostgreSQL persistants : le démarrage n'accepte du trafic qu'après application
des migrations `0001` et `0002`, dont `0002` crée notamment la table `carts`.

Le Compose local conserve son mode développement et ses repositories en
mémoire ; les migrations peuvent néanmoins être vérifiées séparément avec
`alembic upgrade head`.
