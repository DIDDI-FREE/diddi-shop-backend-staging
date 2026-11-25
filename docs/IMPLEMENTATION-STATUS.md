# DiddiShop — état d’implémentation

**Date :** 2026-11-25
**Phase courante :** S13 terminé localement
**Statut :** implémentation locale complète ; recette staging en attente

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
| `pytest -q` | tests unitaires et contrats | disponible, dernier résultat : 55 passed |
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
- Un `Dockerfile` et un `docker-compose.yml` local fournissent PostgreSQL,
  Redis et l’API en mode développement ; l’image est construite, les
  migrations sont appliquées et les trois conteneurs sont healthy. Les
  endpoints `/health` et `/ready` répondent 200.
- Alembic utilise désormais le moteur asynchrone PostgreSQL avec
  `run_sync`, ce qui permet l’exécution réelle des migrations avec le même
  `postgresql+asyncpg` que l’application.
- Le portail documentaire MkDocs est construit dans `Dockerfile.docs` puis
  servi par Nginx dans un conteneur séparé. La vérification locale sur le port
  `18082` répond 200 pour `/` et `/api/API_CONTRACT/`.
- Le Compose de staging n’expose plus de port hôte pour l’API ou la
  documentation. L’overlay `docker-compose.proxy.yml` utilise un réseau
  externe configurable `NPM_NETWORK` ; Nginx Proxy Manager cible `api:8000` et
  `docs:80`.

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
- fourniture par l’infrastructure du nom exact du réseau Docker partagé avec
  Nginx Proxy Manager (`NPM_NETWORK`).
