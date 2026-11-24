# PHASE 6A — finance métier

**Statut :** terminé

Annulation avant pickup, restitution idempotente du stock, annulation de la
livraison et demande de remboursement sont orchestrées dans `FinanceService`.
Les réclamations ouvertes passent la commande en `DISPUTED` et bloquent la
release.
