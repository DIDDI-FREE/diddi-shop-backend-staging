# S24-N — paiement : preuve de bout en bout et garde-fous

- Reproduire création et retry via les routes réelles, les repositories SQL,
  le port DiddiPay réel et un transport HTTP simulé (aucun paiement réel).
- Couvrir téléphone transmis, checkout historique, absence/invalidité du
  téléphone, réponse fournisseur avec téléphone nul et rejeu idempotent.
- Refuser un paiement sans téléphone valide avant tout effet métier.
- Identifier explicitement un rejeu de réponse sans casser la déduplication.
- Vérifier la relecture SQL, tester localement et dans Docker Desktop isolé.
- Mettre à jour MkDocs, décisions et état ; commit/push si vérifications vertes.
- Portainer : lectures uniquement ; aucune action de déploiement.
