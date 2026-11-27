# S24-P — webhook paiement persistant et parcours vendeur/livraison

- Reproduire le webhook signé `payment.succeeded` avec les repositories SQL,
  l'inbox et l'outbox réels, sans appel externe ni état staging fabriqué.
- Vérifier les types restaurés après JSON : commande, boutique, projection de
  livraison, et les pertes de modifications dues au rechargement d'agrégats.
- Tester les routes citées dans le rapport : boutiques vendeur, commandes,
  autorisation acheteur/vendeur, confirmation, ready et suivi DiddiSend.
- Corriger uniquement DiddiShop et les défauts démontrés dans ce parcours.
  Préserver les états métier et les contrôles de signature/idempotence.
- Tester panne avant sauvegarde et rejeu du même événement, puis suite Docker
  isolée, lint, compilation, MkDocs et migrations SQL.
- Documenter la reprise du vrai webhook déjà payé : ne pas relancer un paiement
  pour réparer sa notification. Commit/push ; aucun déploiement Portainer.
