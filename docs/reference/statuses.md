# États de référence

## Produit

| État | Signification |
| --- | --- |
| `draft` | article créé mais non publié |
| `published` | article visible dans le catalogue |
| `paused` | article temporairement masqué |
| `retired` | article définitivement retiré |

Le stock nul ne constitue pas un état produit distinct.

La commande utilise deux machines séparées. Les valeurs ci-dessous sont les
valeurs du domaine local et ne doivent pas être remplacées par un statut
propriétaire DiddiSend ou DiddiPay sans mapping explicite.

## FulfillmentStatus

| État | Signification | Terminal |
| --- | --- | --- |
| `PAYMENT_PENDING` | paiement initial non confirmé | non |
| `TO_CONFIRM` | paiement confirmé, attente de confirmation vendeur | non |
| `TO_PREPARE` | vendeur a confirmé, préparation en cours | non |
| `READY_FOR_PICKUP` | vendeur a signalé « prête » ; DiddiShop demande DiddiSend | non |
| `PICKED_UP` | colis remis à la livraison | non |
| `IN_TRANSIT` | livraison en transit | non |
| `DELIVERED` | livraison remise | non |
| `RETURNED` | colis retourné | oui, avant fermeture |
| `FAILED` | échec opérationnel de livraison | oui, avant fermeture |
| `DISPUTED` | réclamation ouverte après livraison | non |
| `CANCELLED` | commande annulée | oui |
| `CLOSED` | dossier terminé après retour, échec ou litige | oui |

## PaymentStatus

`PENDING`, `HELD`, `REFUND_PENDING`, `REFUNDED`, `PARTIALLY_REFUNDED`,
`RELEASE_BLOCKED`, `RELEASE_PENDING` et `RELEASED` sont conservés séparément.
Les états `RELEASE_*` sont réservés au port V2 ; aucun de ces états ne doit
déclencher une séquestration en V1.

Le traitement actuel de `payment.succeeded` utilise déjà `HELD` comme nom
historique local pour la commande payée, avec `fulfillment_status=TO_CONFIRM`.
Pour le frontend, le checkout expose `status=payment_succeeded`. Aucun appel
de hold ou release vendeur n'est déclenché par cette confirmation en V1.

## Transitions autorisées

```text
PAYMENT_PENDING -> TO_CONFIRM | CANCELLED
TO_CONFIRM -> TO_PREPARE | CANCELLED
TO_PREPARE -> READY_FOR_PICKUP | CANCELLED
READY_FOR_PICKUP -> PICKED_UP | RETURNED | FAILED | CANCELLED
PICKED_UP -> IN_TRANSIT | DELIVERED | RETURNED | FAILED
IN_TRANSIT -> DELIVERED | RETURNED | FAILED
DELIVERED -> DISPUTED | CLOSED
DISPUTED -> CLOSED
RETURNED -> CLOSED
FAILED -> CLOSED
```

Une notification externe ne remplace jamais une transition locale validée.
Après timeout, relire la commande et l’opération externe avant tout rejeu.
