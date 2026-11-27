# Parcours checkout et commande

Ce parcours décrit l’orchestration DiddiShop. Les systèmes externes restent
propriétaires de leurs propres statuts.

## Séquence

```text
Acheteur
  │
  ├─ panier et campagne explicite éventuelle
  │
  ▼
DiddiShop checkout
  ├─ vérifie catalogue et stock
  ├─ fige prix, frais et devise XOF
  ├─ quote/réserve Rewards si demandé
  ├─ crée PaymentIntent DiddiPay avec clé stable
  └─ crée une commande par boutique
        │
        ▼
  payment.succeeded
        │
        ▼
  TO_CONFIRM → TO_PREPARE
                     │
                     │ vendeur signale « prête » dans l’application
                     ▼
              POST /v1/orders/{id}/ready
                     │
                     ▼
              DiddiShop crée DiddiSend
```

## Règles de reprise

1. Le client fournit `idempotency_key` à `POST /v1/checkouts`.
2. Après un timeout DiddiPay, DiddiShop relit l’intention ou réutilise la
   même clé ; il ne crée pas une nouvelle intention aveuglément.
3. Un checkout multi-boutiques produit un agrégat de commande par boutique,
   avec ses propres références logistiques.
4. Une confirmation de paiement ne confirme pas que le vendeur a préparé le
   colis.
5. Le vendeur ne crée pas directement la livraison. Il signale que la commande
   est prête via `POST /v1/orders/{order_id}/ready`.
6. DiddiShop valide le passage à `READY_FOR_PICKUP`, appelle immédiatement
   DiddiSend avec `shop:create-delivery:{order_id}:1` et persiste `delivery_id`.
7. Un rejeu du signal vendeur est idempotent : si la projection existe déjà,
   DiddiShop ne crée pas une seconde livraison.
8. `POST /v1/deliveries/orders/{order_id}` reste une opération de reprise
   contrôlée pour l’exploitation ; l’application vendeur ne doit pas l’appeler.

## Téléphone et rejeu de paiement

Le paiement transmet `recipient_phone` sous le nom DiddiPay `customer_phone`.
Le retry récupère la donnée conservée ; s'il ne trouve aucun téléphone valide,
il répond `422 PAYMENT_PHONE_REQUIRED` sans tenter un nouveau paiement.

Un retry HTTP 200 ne prouve pas qu'une nouvelle tentative a eu lieu : vérifier
`Idempotency-Replayed`. `true` restitue une réponse déjà enregistrée ; `false`
identifie une nouvelle opération. Après un échec confirmé, utiliser une
nouvelle clé ; après un timeout, conserver la clé pour éviter un double paiement.

## Snapshot financier

Le snapshot de commande conserve au minimum le prix des lignes, le total,
les frais de livraison, la commission et l’avantage Rewards appliqué. Tous les
montants sont XOF. Le catalogue courant ne doit jamais être relu pour
recalculer une commande existante.

## Expédition

DiddiShop envoie à DiddiSend `origin_module=diddishop`,
`payment_method=diddipay`, `prepaid_by_origin=true` et une clé stable. Le
contrat de ventilation financière DiddiSend doit être vérifié en recette
staging ; la devise est XOF et le mode d’expédition est prépayé par DiddiShop
(`prepaid_by_origin=true`).

## Événements de suivi

Les événements DiddiPay et DiddiSend sont reçus par webhook signé, dédupliqués
par l’inbox puis appliqués à la commande. L’ordre d’arrivée d’un événement
externe ne doit pas autoriser une transition illégale ; dans ce cas, l’état est
mis en attente/réconciliation et l’incident est audité.
