# DiddiShop — état d’implémentation

**Date :** 2026-11-26
**Phase courante :** S23-D terminé localement
**Statut :** implémentation locale complète ; recette staging en attente

**Correction du 2026-11-27 :** le Compose staging exécute désormais
`alembic upgrade head` avant Uvicorn. L'incident staging `relation "carts"
does not exist` venait de l'absence de cette étape au démarrage, pas d'un
problème JWT ou DiddiSend.

## État global

Le squelette Clean Architecture existe sous `app_base/`. Les frontières sont
définies pour boutiques, catalogue, panier, checkout, commandes, réclamations,
Rewards/campagnes, communication, support, observabilité, audit et backoffice.

La seule frontière logistique de DiddiShop est DiddiSend. DiddiShop ne dépend
pas d’un service de flotte ou de coursiers.

Les phases S0 à S8 sont implémentées localement : persistance SQL, workers
outbox/inbox, authentification, contrats S2S, checkout, paiements, expédition,
finance, transverse et backoffice. Les opérations financières externes qui
dépendent d’un contrat marketplace non confirmé restent protégées derrière
leurs ports.

## Commandes de vérification identifiées

| Commande | Usage | État |
| --- | --- | --- |
| `python -m compileall -q app_base tests alembic` | compilation Python | disponible, OK |
| `pytest -q` | tests unitaires et contrats | disponible, dernier résultat : 71 passed |
| `ruff check .` | lint | disponible, dernier résultat : OK |
| `alembic upgrade head --sql` | vérification des migrations | disponible, OK |
| `alembic upgrade head` | migrations réelles | OK dans PostgreSQL local Compose |
| tests PostgreSQL/Redis | intégration | OK via le Compose local |

## Phases S0 à S8 réalisées

- plan et documents d’architecture lus ;
- dépôt inspecté ;
- dépôt Git local initialisé et synchronisé avec le remote GitHub ;
- fichiers de suivi créés ;
- décisions existantes extraites ;
- questions initiales et décisions intégrées dans `docs/decisions/DECISIONS.md`.
- journaux et plans de lots conservés dans `tasks/`.

## Blocages et contrats à valider

1. DiddiSend : confirmation du mode prépayé et de la ventilation financière
   XOF pour DiddiShop ; aucune conversion de devise ne sera acceptée.
2. DiddiFiles : visibilité et URL finale des images
   `diddishop_product_image`.
3. DiddiFreeID : provisionnement des clients et scopes S2S supporté par le
   code ; il reste à injecter les valeurs dans le secret manager staging.
4. DiddiObserve : l’ingestion centrale est rétablie. Il reste à injecter le
   credential OTLP Basic dédié hors Git et à vérifier les marqueurs synthétiques
   API/worker ainsi que la corrélation réelle dans Loki/Tempo.
5. DiddiRewards : confirmer le provisioning du client Shop, une campagne
   publiée avec budget, et le contrat de ventilation `professional_payout_minor`
   en V1.

## S0 réalisé

- DiddiMap retiré du registre et de la configuration.
- URLs HTTPS staging documentées dans `.env.example`.
- Configuration non développement fail-closed sur les URLs externes.
- Initialisation de l’outbox corrigée.

## Réalisations S1 à S12

- PostgreSQL/Alembic pour les agrégats métier, inbox, outbox, idempotence et audit ; Redis pour la publication et la coordination des workers.
- JWT/JWKS DiddiFreeID, scopes S2S dédiés et signatures HMAC des webhooks.
- Obtention dynamique DiddiFreeID `client_credentials` par cible, cache court,
  `X-Client-ID` et fail-closed en staging si un client ou secret manque.
- DiddiFiles pour les sessions d’upload, confirmation, métadonnées et URLs.
- Checkout multi-boutiques, snapshots de prix, PaymentIntent DiddiPay et machine d’états commande/paiement.
- DiddiSend comme unique propriétaire de l’expédition, avec livraison prépayée et suivi persistant.
- Annulations, retours, réclamations et refunds idempotents ; séquestration/release vendeur explicitement reportées en V2.
- DiddiRewards utilise les routes dédiées DiddiShop, les snapshots de campagne
  versionnés et le cycle quote/reserve/confirm/release/correct ; DiddiShop
  impose XOF exclusivement. DiddiSupport, DiddiObserve et DiddiBackoffice
  conservent leurs frontières, audit et idempotence ; DiddiComms est limité à
  l’ouverture/récupération de conversations métier.
- DiddiObserve utilise le SDK OpenTelemetry en OTLP HTTP/protobuf, avec files
  bornées, retry réseau/429/502/503/504, timeout de requête de 5 secondes,
  flush d’arrêt borné et credential Basic dédié hors Git. Aucun client ou scope
  S2S DiddiFreeID n’est utilisé pour la télémétrie.
- Les OpenAPI staging ont été sondées sans credentials métier. DiddiPay est
  aligné sur `amount` et la normalisation de ses identifiants de réponse ; les
  routes DiddiSend, DiddiFiles, DiddiRewards, DiddiComms et DiddiSupport sont
  couvertes par des tests de câblage avec faux services.
- Un `Dockerfile` et un `docker-compose.local.yml` fournissent PostgreSQL,
  Redis et l’API en mode développement ; l’image est construite, les
  migrations sont appliquées et les trois conteneurs sont healthy. Les
  endpoints `/health` et `/ready` répondent 200.
- Alembic utilise désormais le moteur asynchrone PostgreSQL avec
  `run_sync`, ce qui permet l’exécution réelle des migrations avec le même
  `postgresql+asyncpg` que l’application.
- Le portail documentaire MkDocs est construit dans `Dockerfile.docs` puis
  servi par Nginx dans un conteneur séparé. La vérification locale sur le port
  `48182` répond 200 pour `/` et `/api/API_CONTRACT/`.
- La stack canonique `docker-compose.yml` reprend le modèle DiddiGo : API et
  MkDocs sont construits dans la même stack et depuis la même révision Git.
  `DOCS_PUBLIC_ENABLED` reste désactivé par défaut et doit être activé
  explicitement en staging.
- `portainer.env.example` contient les valeurs staging non sensibles et la
  forme exacte des secrets à injecter ; `portainer.env` est local et ignoré.
- Le Compose Portainer transmet explicitement les paramètres de sécurité,
  délais métier, finance V1 et observabilité ; les secrets DiddiFreeID,
  webhooks et OTLP restent des variables obligatoires à injecter hors Git.

## Dernier lot implémenté — S24-C

Le webhook DiddiPay lit désormais `DIDDI_SHOP_DIDDIPAY_WEBHOOK_SECRET`, vérifie
`X-DiddiPay-Signature` sur les octets exacts du corps sans timestamp, puis
adapte l’enveloppe `{id, type, occurred_at, data}` émise par DiddiPay vers le
contrat interne. La référence `diddishop:checkout:{checkout_id}` est résolue
pour rattacher l’événement au checkout. Le secret webhook entrant reste
distinct des credentials S2S sortants.
- Le Compose local est séparé sous `docker-compose.local.yml` ; le fichier
  `docker-compose.yml` est réservé à Portainer/staging et transmet toutes les
  variables nécessaires à l’API.
- La surface frontend V1 expose maintenant les listes catalogue/boutique,
  boutiques et produits vendeur, modification prix/stock, suppression de
  ligne panier, listes de commandes, commandes à confirmer, upload/attachement
  DiddiFiles, réponse checkout/paiement normalisée et codes d’erreur stables.
- Le Compose publie par défaut des ports hôte élevés et configurables
  (`48180` pour l’API et `48182` pour la documentation), afin de fonctionner
  même sans accès au réseau Docker de Nginx Proxy Manager. L’overlay
  `docker-compose.proxy.yml` reste disponible lorsque ce réseau est fourni.
- CORS autorise les sous-domaines `*.diddifree.com` et `localhost` avec port
  optionnel, accepte le préflight et le header `Authorization`, sans activer
  les credentials navigateur.

## Dernier lot implémenté — S24-D

Le scope DiddiSend demandé par DiddiShop pour la création est désormais
`diddisend:deliveries:create`, conformément à la route DiddiSend, et non
`diddisend:deliveries:write`. Le client utilise l’identité dédiée
`diddishop-staging-diddisend`, l’audience `diddisend`, l’origine `diddishop`
et un UUID technique transmis dans `X-User-ID` et `sender_user_id`. Le
callback entrant est vérifié avec `X-DiddiSend-Signature` et un secret HMAC
séparé. Il reste à injecter les valeurs secrètes côté Portainer/DiddiSend et
à rejouer la recette E2E après redéploiement.

## S24-E — correction JWT/JWKS runtime

Le `401` observé sur `GET /v1/cart` provenait de DiddiShop pendant la
validation du JWT acheteur. L’image chargeait un chemin incompatible avec les
versions récentes de PyJWT (`jwt.algorithms.RSAAlgorithm`). Le validateur
utilise désormais `PyJWK.from_dict`, et le Dockerfile vérifie la présence de
PyJWT au build. Aucun changement Portainer n’a été effectué.

## Réponses intégrées

- release vendeur : port conservé pour V2, désactivé par défaut en V1 ;
- expédition : modèle DiddiFood adapté à `origin_module=diddishop` ;
- infrastructure : PostgreSQL + Redis ;
- S2S : scopes dédiés par service ;
- Git : initialisation locale et remote GitHub fourni.

## Vérifications de déploiement en attente

- provisionnement PostgreSQL/Redis ;
- migrations sur staging ;
- configuration des credentials et scopes S2S ;
- tests de bout en bout avec DiddiPay, DiddiSend, DiddiFiles et DiddiRewards ;
- vérification des workers outbox/inbox, DLQ et alertes ;
- validation de la ventilation XOF DiddiSend ; le contrat marketplace DiddiPay est hors MVP et planifié en V2 ;
- validation du contrat DiddiRewards Shop en staging avec quote, reserve,
  confirm, release et correct ;
- injection de `secrets/onboarding/diddishop.env` par Compose, déploiement,
  SHA/contact/marqueurs synthétiques API et worker DiddiObserve ;
- exposition des endpoints Prometheus, token de scrape distinct et test
  refus/succès avant activation du scrape DiddiShop ;
- vérification de la corrélation traceparent/trace_id/span_id, de l’absence de
  données sensibles et du comportement collecteur indisponible sans transaction
  réelle.
- publication du conteneur docs sur `docs-diddishop-staging.diddifree.com`,
  Proxy Host Nginx, certificat TLS et vérification externe des pages.
- redéploiement de la stack Portainer `diddishop-backend` avec le nouveau
  `docker-compose.yml` canonique ; l’audit live a confirmé que la révision
  précédente exécutait encore l’ancien Compose en mode développement.
- choix des ports hôte disponibles si les valeurs par défaut `48180`/`48182`
  sont déjà utilisées ;
- ou fourniture du nom exact du réseau Docker partagé avec Nginx Proxy Manager
  (`NPM_NETWORK`) pour utiliser l’overlay réseau.
- redéploiement de l’image API avec le middleware CORS et vérification du
  préflight depuis l’URL publique.

## S18 — contrats frontend et documentation

- Ajout de schémas de réponse Pydantic explicites dans OpenAPI pour boutiques,
  catégories, produits, photos, panier, commandes et checkout.
- Ajout de `GET /v1/catalog/categories` avec une liste stable de codes et de
  libellés frontend.
- Formalisation des états produit : `draft`, `published`, `paused`, `retired`.
- Alignement du parcours DiddiFiles sur le contrat staging réel : session,
  PUT vers l’URL signée, confirmation puis rattachement par DiddiShop.
- Les listes de produits exposent `photo_urls` lorsqu’une URL publique est
  fournie par DiddiFiles.
- La documentation MkDocs, le contrat API et le changelog ont été mis à jour.

## Vérifications de déploiement en attente — S18

- Redéployer l’image API et le conteneur MkDocs depuis le nouveau commit.
- Vérifier l’OpenAPI et les pages publiques sur
  `https://docs-diddishop-staging.diddifree.com`.
- Vérifier que le staging exige bien le Bearer DiddiFreeID ; `X-Actor-ID` reste
  réservé au développement local.

## S19 — déclenchement DiddiSend après signal vendeur

- Le signal vendeur `POST /v1/orders/{order_id}/ready` passe la commande à
  `READY_FOR_PICKUP` puis appelle automatiquement DiddiSend.
- La clé `shop:create-delivery:{order_id}:1` et la projection `delivery_id`
  rendent le rejeu sûr après timeout.
- La route directe de création livraison reste disponible uniquement comme
  reprise contrôlée d’exploitation.

## S20 — audit documentaire des protocoles et routes

- Les 44 chemins métier présents dans l’OpenAPI sont listés dans
  `docs/api/PROTOCOLS_AND_COVERAGE.md`.
- REST/JSON, webhooks JSON, S2S Bearer, client credentials et OTLP
  HTTP/protobuf sont décrits avec leurs headers et limites.
- L’absence de WebSocket est explicitement documentée.
- Les routes qui dépendaient de réponses génériques ont ensuite été typées en
  S22 ; les dépendances externes restent dans la recette staging.

## S21 — référence détaillée de chaque route

- Ajout de `docs/api/ROUTE_REFERENCE.md` avec méthode, auth, paramètres,
  contraintes, réponses, erreurs et limites pour chaque route métier.
- Les contrôles d’acteur des parcours commande, livraison, claims et checkout
  sont implémentés ; les routes internes utilisent la frontière S2S prévue.
- Les contrats delivery, claims, admin, support et webhooks disposent de
  modèles de réponse OpenAPI explicites.

## S22 — implémentation des contrats frontend incomplets

- Le panier renvoie les titres, prix unitaires, totaux de ligne, sous-totaux par
  boutique et le sous-total global.
- Le checkout exige désormais l’adresse physique, les coordonnées géographiques
  et le téléphone E.164 ; `POST /v1/checkouts/quote` calcule le devis sans
  paiement.
- `GET /v1/checkouts/{id}` lit le paiement ; `/retry` reprend uniquement un
  paiement échoué avec une nouvelle clé, et les créations/reprises sont
  protégées par l’idempotence persistante.
- Les commandes exposent lignes financières, `created_at`, échéance vendeur et
  informations de livraison ; les projections DiddiSend exposent coursier,
  position et code de remise.
- Les annulations exposent `OrderResponse` et les codes
  `ORDER_NOT_CANCELLABLE`/`DELIVERY_ALREADY_PICKED_UP`.
- Les produits disposent de pause/retrait, de huit photos maximum et des
  formats JPEG/PNG/WebP avec limite de 10 MiB.
- Les tests unitaires et contractuels passent : 69 tests.

## S23-A — quantité exacte du panier

- Ajout de `PATCH /v1/cart/lines/{product_id}` avec remplacement exact de la
  quantité, contrôle du stock et réponse `CartResponse` enrichie.
- `DELETE` reste l’opération dédiée à la suppression ; `quantity=0` est refusé.

## S23-B — paiement et commandes

- Le checkout accepte `wave`, `mtn_momo` et `orange_money`, avec `wave` par
  défaut, et contrôle les `return_url` vers DiddiFree ou localhost.
- Les champs DiddiPay optionnels utiles (`payment_url`, `checkout_url`,
  `client_secret`, `payment_method`, `expires_at`) sont relayés sans exposer
  la réponse brute du prestataire.
- `GET /v1/orders` utilise une pagination par curseur opaque et les commandes
  exposent `created_at`, `delivered_at` et `status_history`.

## S23-C — réclamations, preuves et remboursements

- Ajout de la lecture d’une réclamation par commande, du calcul de l’échéance
  à 72 heures, des motifs contrôlés et des codes d’erreur stables.
- Les preuves sont préparées via DiddiFiles, limitées à trois images JPEG/PNG/
  WebP de 10 MiB maximum, et les remboursements exposent un moyen et une
  référence masquée.

## S23-D — suivi DiddiSend

- La projection de livraison normalise le coursier et la position avec un
  schéma stable (`id`, `name`, `phone_masked`, `avatar_url`, `vehicle_type`,
  puis `latitude`, `longitude`, `updated_at`).
- DiddiSend reste la source de vérité du suivi opérationnel ; DiddiShop ne
  conserve qu’une projection nécessaire à l’API frontend.

## S24-F — alignement des JWT utilisateurs DiddiFreeID

- Les JWT acheteurs staging sans claim `aud` sont acceptés sur les routes
  frontend après vérification de signature, `exp`, `sub` et issuer.
- Les routes internes S2S continuent d’exiger explicitement `aud=diddishop`.
- `DIDDI_SHOP_DIDDIFREEID_ISSUER` est obligatoire en staging et vaut
  `diddifree-id` ; une valeur vide provoque désormais un échec de démarrage
  explicite.
- Vérifications locales : 81 tests passés et Ruff OK.
- Le détail sûr du rejet JWT est envoyé à la fois au logger applicatif OTLP
  (`diddi_shop.auth`) et à `uvicorn.error` pour être visible dans
  `docker logs` ; aucun JWT n’est journalisé.
- Le runtime Docker installe explicitement `PyJWT[crypto]` afin de fournir le
  backend RSA requis par les JWT RS256 de DiddiFreeID.

### Vérifications de déploiement en attente — S24-F

- Ajouter `DIDDI_SHOP_DIDDIFREEID_ISSUER=diddifree-id` dans Portainer.
- Reconstruire l’image API depuis ce commit puis rejouer `GET /v1/cart` et
  `GET /v1/orders` avec le JWT acheteur.
- Après redeploiement du diagnostic, lire la cause PyJWT exacte dans les logs
  si le `401` persiste.
- Faire un appel réel `GET /v1/cart` avec un JWT acheteur après ce redeploiement;
  le conteneur contrôlé est healthy, mais ses logs ne contiennent encore aucun
  rejet JWT détaillé postérieur à l’appel de diagnostic.
- Le dernier appel réel a ensuite révélé `MissingCryptographyError` ;
  reconstruire l’image avec la dépendance crypto avant le prochain test.

## S24-G — migrations PostgreSQL au démarrage

- Les migrations Alembic étaient présentes mais n’étaient pas exécutées par le
  Compose staging ; cela expliquait `relation "carts" does not exist` après une
  authentification réussie.
- Le service API exécute maintenant `alembic upgrade head` avant de lancer
  Uvicorn, suivant le modèle DiddiFood staging.
- Vérifications locales : 82 tests passés, Ruff OK, image construite et test
  d’intégration sur PostgreSQL vide réussi (`/health` HTTP 200, deux migrations
  appliquées).

### Vérifications de déploiement en attente — S24-G

- Déployer manuellement le nouveau Compose/image dans Portainer.
- Vérifier les marqueurs Alembic `Running upgrade` dans les logs API.
- Rejouer `GET /v1/cart` avec un JWT acheteur et confirmer l’absence de 500.

## S24-H — correction panier après lecture PostgreSQL

- Les produits relus depuis le payload JSON reconstruisent maintenant
  `ProductStatus` avant d’être utilisés par le panier et le checkout.
- Vérifications locales : 83 tests passés et Ruff OK.

### Vérifications de déploiement en attente — S24-H

- Déployer manuellement le commit sur Portainer.
- Rejouer `POST /v1/cart/lines`, puis le devis checkout.

## S24-I — devis DiddiSend

- L’adaptateur accepte maintenant les réponses numériques et les réponses
  structurées (`quote.amount_minor`, `quote.amount.value`, etc.).
- Une erreur upstream DiddiSend est exposée comme `502
  DELIVERY_QUOTE_UNAVAILABLE`, au lieu d’un HTTP 500 non documenté.
- Vérifications locales : 87 tests passés et Ruff OK.

### Vérifications de déploiement en attente — S24-I

- Déployer manuellement le commit sur Portainer.
- Rejouer le devis avec des coordonnées de retrait et de livraison distinctes.
- Si DiddiMap renvoie encore une distance nulle, corriger les coordonnées du
  scénario de test côté appelant ; ce n’est pas une erreur de parsing Shop.

## S24-J — payload PaymentIntent DiddiPay

- Payload aligné sur l’OpenAPI staging : `channel=mobile_money` et `network`
  selon le moyen choisi. Les champs non contractuels `payment_method` et
  `return_url` ont été retirés.
- `cash` reste volontairement refusé : le MVP utilise uniquement Wave, MTN
  Mobile Money et Orange Money.
- Vérifications locales : `pytest -q` et `ruff check .`.

### Vérifications de déploiement en attente — S24-J

- Déployer manuellement le commit dans Portainer.
- Rejouer le checkout avec `wave`, puis vérifier la création du PaymentIntent.
- Vérifier ensuite `mtn_momo` et `orange_money` sans transaction réelle si le
  fournisseur de paiement l’autorise.

## S24-K — échec PaymentIntent et retry checkout

- Un PaymentIntent retourné avec `status=failed` produit maintenant un checkout
  `payment_failed` sauvegardé avec les trois champs de diagnostic.
- Le retry exige une nouvelle `Idempotency-Key`, sauvegarde `payment_pending`
  avant l'appel fournisseur, puis sauvegarde l'état final selon la réponse.
- Vérifications locales : 88 tests passés, Ruff OK.

### Vérifications de déploiement en attente — S24-K

- Déployer manuellement le commit dans Portainer.
- Créer un checkout qui reçoit `status=failed`, vérifier `GET /v1/checkouts/{id}`
  et confirmer les trois champs d'échec.
- Rejouer `POST /v1/checkouts/{id}/retry` avec une nouvelle clé et vérifier que
  le statut final est `payment_failed` ou `payment_succeeded`.

## S24-L — customer_phone PaymentIntent

- `recipient_phone` est maintenant propagé vers `customer_phone` dans le
  payload DiddiPay/PawaPay.
- Le téléphone est conservé dans le paiement du checkout et réutilisé lors du
  retry.
- Vérifications locales : 88 tests passés, Ruff OK.

### Vérifications de déploiement en attente — S24-L

- Déployer manuellement le commit dans Portainer.
- Rejouer un checkout/retry mobile money avec un téléphone `+237...` et vérifier
  que l'erreur `customer_phone is required` a disparu.
