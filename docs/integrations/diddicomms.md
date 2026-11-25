# Intégration DiddiComms

La route DiddiComms utilisée par DiddiShop ouvre ou retrouve une conversation
attachée à une ressource métier. Elle ne soumet pas une notification SMS,
WhatsApp ou push.

`POST /comms/v1/tasks/{owner_service}/{task_type}/{task_id}/conversation`
n’accepte pas de corps JSON. Les participants viennent du resolver DiddiComms ;
ils ne sont pas fournis dans la requête.

L’intégration événementielle de notifications est donc hors contrat de cette
route. Il faut un contrat séparé pour l’enveloppe d’événement, les canaux,
destinataires, retries, déduplication et résultats de livraison.
