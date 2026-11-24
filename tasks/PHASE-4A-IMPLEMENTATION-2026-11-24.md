# PHASE 4A — checkout et commandes

**Statut :** terminé

Le checkout lit le panier, regroupe par boutique, demande un quote DiddiSend,
décrémente le stock par opération idempotente, crée une commande par boutique
et crée un PaymentIntent via `PaymentIntentPort`.

Les lignes, titres, prix et frais sont stockés dans le metadata snapshot de la
commande. Un échec du paiement restitue le stock avec des opérations séparées.
