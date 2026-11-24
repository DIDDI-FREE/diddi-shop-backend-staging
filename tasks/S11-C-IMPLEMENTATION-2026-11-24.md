# S11-C — journal d'implémentation

- Statut : terminé
- Paiement confirmé : confirmation Rewards avec ventilation et référence
  DiddiPay.
- Paiement échoué ou annulation avant paiement : libération idempotente.
- Remboursement confirmé : correction idempotente par `consumption_id`.
- Limite connue : le payout vendeur vaut zéro en V1 tant que la séquestration et
  la release vendeur sont hors périmètre.
