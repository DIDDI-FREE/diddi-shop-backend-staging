# Intégration DiddiSend

DiddiSend est l’unique propriétaire de l’expédition DiddiShop. DiddiShop ne
connaît ni les coursiers, ni la flotte, ni le géocodage opérationnel.

## Appels

| Opération | Contrat local | Clé |
| --- | --- | --- |
| Quote | `DeliveryQuote` | clé de quote du checkout |
| Création | `DeliveryRequest` | `shop:create-delivery:{order_id}:1` |
| Lecture | projection par `delivery_id` | — |
| Annulation | opération autorisée par DiddiSend | `shop:cancel-delivery:{order_id}:{operation}` |

## Déclenchement depuis l’application vendeur

Le vendeur ne contacte jamais DiddiSend directement. Lorsque la préparation est
terminée, l’application appelle :

```http
POST /v1/orders/{order_id}/ready
Authorization: Bearer <acheteur-ou-vendeur-token>
```

DiddiShop vérifie que la commande est `TO_PREPARE`, la passe à
`READY_FOR_PICKUP`, puis appelle immédiatement DiddiSend avec la clé
`shop:create-delivery:{order_id}:1`. La réponse de DiddiSend est projetée dans
DiddiShop sous `delivery_id`.

Si la requête frontend expire après le changement d’état, le même appel peut
être rejoué. Une projection existante est renvoyée et aucune deuxième livraison
n’est créée. La route `POST /v1/deliveries/orders/{order_id}` est réservée à la
reprise contrôlée par l’exploitation.

Le payload porte `origin_module=diddishop`, `order_reference`, pickup/dropoff,
colis, `payment_method=diddipay`, `quoted_price`,
`prepaid_by_origin=true` et éventuellement `financial_breakdown`.

## Événements

Les événements utiles sont `delivery.created`, `delivery.picked_up`,
`delivery.in_transit`, `delivery.delivered`, `delivery.failed` et
`delivery.returned`. Ils entrent par le webhook signé, passent par l’inbox et
mettent à jour la projection locale.

## Point à valider

Le staging expose encore un schéma de ventilation financière de type Food.
Confirmer la ventilation marketplace XOF et le mode prépayé avant recette
authentifiée. DiddiSend ne doit pas créer un second paiement.
