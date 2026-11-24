# S11-B — journal d'implémentation

- Statut : terminé
- Le checkout réserve un bénéfice uniquement lorsqu'un
  `rewards_campaign_id` explicite est fourni.
- Le montant de paiement est diminué de la remise réservée avant création du
  PaymentIntent.
- La réservation est persistée dans le snapshot de commande et réhydratable
  après redémarrage.
