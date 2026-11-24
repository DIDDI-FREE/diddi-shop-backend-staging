# DiddiShop — carte des intégrations observées

Cette carte traduit le code existant en règles d’architecture DiddiShop.

## Composition des intégrations

DiddiShop compose ses intégrations selon le chemin suivant :

```text
lifespan -> app.state (clients, redis, DB)
         -> factories de repositories
         -> factories de services
         -> routers FastAPI
```

DiddiShop l’implémente dans :

- `app_base/core/lifespan.py` : création du registre d’adaptateurs ;
- `app_base/core/integration_registry.py` : composition unique des clients ;
- `app_base/core/deps.py` : injection des services dans les routes ;
- `app_base/modules/*/domain_interfaces.py` : ports consommés par les cas d’usage.

## Flux principal d’une commande

```text
Acheteur
  |
  v
DiddiShop checkout
  |-- stock atomique + snapshot prix
  |-- DiddiRewards.quote/reserve (optionnel)
  |-- DiddiPay.payment-intent (Idempotency-Key)
  v
orders: PAYMENT_PENDING
  |
  +-- payment.succeeded --------------------> TO_CONFIRM
  |                                             |
  |                                             +-- vendeur confirme
  |                                             v
  |                                        TO_PREPARE
  |                                             |
  |                                  ready-for-pickup
  |                                             v
  +-------------------------------------- DiddiSend
                                                |
                                  delivery.* events
                                                v
                             PICKED_UP / IN_TRANSIT / DELIVERED
                                                |
                              claim window / seller release
                                                v
                                 DiddiPay refund ou release
```

## Matrice de possession

| Donnée/commande | Propriétaire | DiddiShop consomme |
| --- | --- | --- |
| Produit, stock, prix de commande | DiddiShop | — |
| PaymentIntent, webhook, refund technique | DiddiPay | statut et confirmation |
| Hold/release marketplace | DiddiPay après contrat à définir | résultat de release |
| Quote/delivery/status coursier | DiddiSend | quote et événements |
| Disponibilité chauffeur | DiddiSend | jamais exposée au domaine Shop |
| Binaire produit/photo | DiddiFiles | metadata et URL |
| Campaignes, benefits, ledger Rewards | DiddiRewards | quote, reservation, consume/release |
| Tâche SMS/notification | DiddiComms | création et résultat |
| Cas support et actions agent | DiddiSupport | contexte, décision, référence |
| Logs/traces/metrics | DiddiObserve | export structuré |
| Identité et tokens S2S | DiddiFreeID | principal/token |
| Vue opérateur et audit opérateur | DiddiBackoffice | commandes admin DiddiShop |

## Adaptateurs et idempotence

| Adaptateur | Clé minimale sortante | Réponse/événement attendu |
| --- | --- | --- |
| DiddiPay create | `shop:create-payment:{checkout_id}:1` | `payment.succeeded` / `payment.failed` |
| DiddiPay refund | `shop:refund:{order_id}:{operation}` | `payment.refunded` |
| DiddiPay release | `shop:release:{order_id}:1` | `seller.release.completed` |
| DiddiSend create | `shop:create-delivery:{order_id}:1` | `delivery.created` puis progression |
| DiddiSend cancel | `shop:cancel-delivery:{order_id}:{operation}` | `delivery.cancelled` |
| DiddiRewards reserve | `shop:reward-reserve:{checkout_id}:1` | reservation idempotente |
| DiddiComms task | `shop:notify:{event_id}:1` | receipt/task status |
| DiddiSupport case | `shop:claim-case:{claim_id}:1` | case reference |

## Gaps explicitement isolés

1. **DiddiPay** expose actuellement PaymentIntent/refund/payout, mais le
   contrat marketplace de release vendeur n’est pas encore explicite. Le port
   `request_release` lève volontairement `NotImplementedError` tant que ce
   contrat n’est pas validé.
2. **DiddiSend** refuse actuellement que DiddiShop lui délègue un paiement
   déjà encaissé ; il faut un mode `prepaid_by_origin` ou équivalent.
3. **DiddiFiles** connaît le purpose `diddishop_product_image`, mais la lecture
   publique de ce purpose doit être confirmée. Le port est donc séparé de la
   décision de visibilité.
4. **DiddiObserve** est traité comme un sink de télémétrie. Le protocole concret
   peut évoluer sans changer les domaines Shop.
