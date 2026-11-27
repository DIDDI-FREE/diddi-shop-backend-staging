# S24-O — retour navigateur Payment Page

- Vérifier l'OpenAPI DiddiPay staging et le resolver `return_target`/`callback_url`
  en lecture seule ; ne modifier aucun autre dépôt ni Portainer.
- Corriger le mapping de `return_url` vers `callback_url`, supporter la cible
  serveur `return_target`, sans jamais envoyer les deux.
- Préserver les entrées au checkout/retry, restaurer les anciens snapshots,
  permettre de préciser une destination au retry sans recréer la commande.
- Valider avant effet métier ; config de repli explicite, sans URL inventée.
- Transmettre `next_action` et l'URL de la Payment Page au frontend.
- Tests routes + SQL + vrai adaptateur/HTTP simulé, puis suite Docker isolée.
- Mettre à jour Compose/templates, MkDocs, décisions et suivi ; commit/push.
- Choix délégué par l'utilisateur : modèle des autres modules. Héberger une
  page neutre `/payments/return` sur le domaine HTTPS du backend Shop, comme
  DiddiSend ; configurable ensuite, sans affirmer qu'un target Pay existe.
