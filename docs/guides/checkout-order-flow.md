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
  TO_CONFIRM → TO_PREPARE → READY_FOR_PICKUP
                                      │
                                      ▼
                              création DiddiSend
```

## Règles de reprise

1. Le client fournit `idempotency_key` à `POST /v1/checkouts`.
2. Après un timeout DiddiPay, DiddiShop relit l’intention ou réutilise la
   même clé ; il ne crée pas une nouvelle intention aveuglément.
3. Un checkout multi-boutiques produit un agrégat de commande par boutique,
   avec ses propres références logistiques.
4. Une confirmation de paiement ne confirme pas que le vendeur a préparé le
   colis.
5. Une commande prête est le seul point à partir duquel le use case livraison
   peut demander DiddiSend.

## Snapshot financier

Le snapshot de commande conserve au minimum le prix des lignes, le total,
les frais de livraison, la commission et l’avantage Rewards appliqué. Tous les
montants sont XOF. Le catalogue courant ne doit jamais être relu pour
recalculer une commande existante.

## Expédition

DiddiShop envoie à DiddiSend `origin_module=diddishop`,
`payment_method=diddipay`, `prepaid_by_origin=true` et une clé stable. Le
contrat de ventilation financière DiddiSend reste à confirmer en staging.

## Événements de suivi

Les événements DiddiPay et DiddiSend sont reçus par webhook signé, dédupliqués
par l’inbox puis appliqués à la commande. L’ordre d’arrivée d’un événement
externe ne doit pas autoriser une transition illégale ; dans ce cas, l’état est
mis en attente/réconciliation et l’incident est audité.
