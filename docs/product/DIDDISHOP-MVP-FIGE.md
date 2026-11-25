# DiddiShop — MVP V1 figé

**Version :** `1.0.0`  
**Devise :** XOF uniquement  
**Séquestration marketplace :** hors MVP, V2

## Promesse du MVP

DiddiShop permet à un acheteur de consulter un catalogue de produits physiques,
constituer un panier, payer via DiddiPay, faire préparer la commande par une
boutique et recevoir la livraison opérée par DiddiSend.

## Inclus en V1

- boutiques, membres vendeur et permissions locales ;
- catalogue produit, publication, médias DiddiFiles et stock ;
- panier et checkout multi-boutiques ;
- un PaymentIntent DiddiPay par parcours de checkout selon le contrat validé ;
- une commande DiddiShop par boutique ;
- expédition exclusivement via DiddiSend ;
- machine à états logistique et statut financier séparés ;
- annulation, retour, réclamation et refund idempotents ;
- avantages et campagnes DiddiRewards lorsque le checkout reçoit une campagne
  explicite ;
- contexte support, audit opérateur et observabilité ;
- routes DiddiBackoffice via l’API DiddiShop, sans accès direct aux tables.

## Exclus de V1

- séquestration des fonds ;
- release ou payout vendeur marketplace ;
- flotte, matching, géocodage et calcul d’itinéraire dans DiddiShop ;
- notification SMS/WhatsApp événementielle non contractualisée ;
- conversion de devise ou devise autre que XOF ;
- accès direct aux bases de DiddiPay, DiddiSend, Rewards ou Support ;
- traitement de données carte dans DiddiShop.

## Propriétaire de chaque capacité

```text
DiddiShop   : panier, catalogue, commande, décision métier
DiddiPay    : PaymentIntent, statut du paiement, refund technique
DiddiSend   : devis, livraison, coursier, suivi et retour opérationnel
DiddiFiles  : binaire et URLs de fichier
DiddiRewards: campagnes, benefits et ledger
DiddiComms  : conversation et transport des communications
DiddiSupport: cas support et décisions opérateur support
DiddiObserve: logs, traces et métriques
DiddiFreeID : identité et credentials S2S
```

## Règles financières

1. Toute valeur monétaire exposée par DiddiShop porte `currency=XOF`.
2. Un prix de commande est un snapshot ; une modification du catalogue ne
   change pas une commande existante.
3. DiddiSend ne doit pas recréer un paiement pour une commande déjà payée.
4. Un remboursement confirmé est distinct de la décision locale d’annuler ou
   d’accepter une réclamation.
5. Aucun mécanisme de hold/release vendeur ne doit être activé en V1.

## Passage en V2

La V2 pourra ajouter la séquestration marketplace et la release vendeur après
un contrat DiddiPay séparé couvrant autorisations, ledger, idempotence,
réconciliation, litiges et événements. Le port existe pour préserver cette
évolution, mais son activation V1 est interdite.
