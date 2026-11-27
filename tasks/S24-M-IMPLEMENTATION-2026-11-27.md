# S24-M — Réconciliation des checkouts historiques

## Diagnostic

Les logs staging montrent un retry direct retournant 409, sans création de
checkout après le démarrage de l'image corrigée. Le checkout existait déjà et
avait conservé `payment_pending` malgré un paiement enregistré `failed`.

## Implémentation

- `CheckoutApplicationService.get` dérive le statut depuis le paiement quand
  le statut local est encore pending.
- La réparation est sauvegardée avant la réponse ; la route retry réutilise
  donc automatiquement le statut `payment_failed` réparé.
- Ajout d'un test de compatibilité pour un checkout historique.

## Vérifications

- `pytest -q` : 89 passed.
- `ruff check .` : OK.
- Déploiement Portainer : manuel par l'utilisateur uniquement.
