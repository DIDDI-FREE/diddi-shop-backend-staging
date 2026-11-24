# PHASE 1B — Redis et idempotence

**Statut :** terminé

Le port `RedisPort`, l’adaptateur Redis Streams/verrou et les contrats
d’idempotence sont disponibles. Le test utilise un faux store et ne requiert
pas Redis local.

**Vérification :** `pytest -q` → `4 passed`.
