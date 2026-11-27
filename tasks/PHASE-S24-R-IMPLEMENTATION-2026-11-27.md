# S24-R — journal d’implémentation

## A/B/C — terminé

- `INSUFFICIENT_STOCK` retourne HTTP 422 avec les quantités utiles.
- `expires_at` est normalisé en ISO UTC ; aucun état financier local expiré
  n’est inventé.
- Le téléphone complet et le moyen de paiement sont exposés dans le paiement.
- Le retry accepte un autre moyen de paiement avec une nouvelle idempotence.
- Tests ciblés : 48 passed.

## Déploiement

Déploiement manuel utilisateur en attente. Aucun appel financier réel effectué.
