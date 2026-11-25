# Parcours annulation, retour, réclamation et remboursement

Le domaine local décide de l’éligibilité ; DiddiPay exécute le remboursement
technique ; DiddiSend fournit l’état logistique. La décision locale et le
résultat financier sont donc deux étapes distinctes.

## Annulation

`POST /v1/claims/orders/{order_id}/cancel` enregistre la raison puis demande
la transition autorisée. Avant la prise en charge, DiddiShop peut annuler la
livraison si DiddiSend l’autorise et demander le refund avec la clé
`shop:refund:{order_id}:cancellation`.

Un timeout ne prouve pas que le refund a échoué. Il faut d’abord relire
DiddiPay avec la référence connue et réutiliser la même clé si le contrat le
permet.

## Réclamation

1. L’acheteur ouvre la réclamation avec une raison.
2. DiddiShop vérifie la fenêtre et l’absence de réclamation ouverte concurrente.
3. Support ou backoffice décide `buyer`, `seller`, `partial` ou `rejected`.
4. Une décision avec montant positif déclenche un refund idempotent.
5. La commande devient `DISPUTED`, puis `CLOSED` après traitement.

Le montant de remboursement est un entier XOF et ne peut pas être négatif. La
réclamation ne modifie pas la commande ou le catalogue sans use case explicite.

## Retour

Un retour opérationnel est signalé par DiddiSend (`delivery.returned`) puis
projeté localement en `RETURNED`. La restitution du stock et le remboursement
doivent être idempotents et audités séparément.

## V1 et V2

La V1 ne séquestre pas les fonds et ne déclenche pas de release vendeur. Une
décision de réclamation ne doit donc jamais appeler un payout marketplace.
