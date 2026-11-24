# PHASE 7A — Rewards, communication et support

**Statut :** terminé

Rewards reste propriétaire du moteur de campagnes et du ledger ; DiddiShop
conserve seulement une réservation/snapshot utile au checkout. Les événements
Shop peuvent être transformés en tâches DiddiComms idempotentes. Le contexte
Support agrège les projections Shop et les références externes sans écrire dans
les bases de DiddiPay, DiddiSend ou DiddiFiles.
