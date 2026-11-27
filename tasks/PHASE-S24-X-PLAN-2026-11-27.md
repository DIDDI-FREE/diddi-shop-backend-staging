# S24-X — Rejeu DiddiSend et visibilité du paiement d’origine

## Objectif

Rendre l’échec de création DiddiSend explicite côté DiddiShop et isoler le
blocage de lecture du PaymentIntent entre DiddiPay et DiddiSend.

## Sous-lots

- [x] A — auditer le contrôle `client_id` de lecture DiddiPay et l’appel
  DiddiSend.
- [x] B — mapper les statuts HTTP de création DiddiSend vers une erreur Shop
  stable et testée.
- [x] C — documenter le contrat externe manquant et les vérifications staging.

## Hors périmètre

Aucun changement dans DiddiPay, DiddiSend ou Portainer. Aucun secret et aucun
nouveau paiement ne sont ajoutés.
