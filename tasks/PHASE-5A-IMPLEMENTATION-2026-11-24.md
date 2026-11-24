# PHASE 5A — paiement et livraison

**Statut :** terminé

Les webhooks DiddiPay et DiddiSend sont dédoublonnés par consommateur et
`event_id`. Les commandes passent de paiement pending à held/to-confirm sur
`payment.succeeded`, tandis que les événements DiddiSend alimentent uniquement
une projection locale et les transitions autorisées de commande.

La vérification de signature des callbacks doit être branchée sur les secrets
de staging avant activation réelle.
