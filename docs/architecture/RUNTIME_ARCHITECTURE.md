# Architecture d’exécution DiddiShop

**Sources :** `app_base/main.py`, `app_base/core/lifespan.py`,
`app_base/core/deps.py`, `app_base/core/integration_registry.py` et
`app_base/core/settings.py`.

DiddiShop est un monolithe modulaire Clean Architecture. Le déploiement est
unique au MVP, mais les métiers sont séparés par des ports et des contrats.
Cette page décrit le code présent ; elle n’ajoute pas de fonctionnalité
produit.

## Entrée HTTP

`app_base.main:app` crée FastAPI, installe la corrélation de requête et le
middleware OpenTelemetry, puis monte explicitement les routeurs. Les endpoints
d’infrastructure sont :

- `GET /health` : le processus répond ;
- `GET /ready` : PostgreSQL et Redis répondent ;
- `GET /openapi.json` : contrat runtime généré par FastAPI.

## Composition au démarrage

```text
lifespan
  ├── Settings + validation d’environnement
  ├── moteur PostgreSQL async + session factory
  ├── client Redis
  ├── IntegrationRegistry
  │     ├── DiddiFreeID
  │     ├── DiddiPay
  │     ├── DiddiSend
  │     ├── DiddiFiles
  │     ├── DiddiRewards
  │     ├── DiddiComms
  │     ├── DiddiSupport
  │     └── DiddiObserve
  ├── repositories et services
  └── app.state consommé par les dépendances FastAPI
```

Les adaptateurs sont construits une seule fois dans
`core/integration_registry.py`. Les routes récupèrent les services via
`core/deps.py`; elles n’instancient pas directement de client HTTP.

## Couches et direction des dépendances

```text
HTTP / webhooks / workers
          ↓
presentation
          ↓
application
          ↓
domain + ports locaux
          ↑
infra repositories + integrations
```

Règles :

- le domaine ne connaît ni FastAPI, ni SQLAlchemy, ni Redis, ni HTTP ;
- un module ne lit pas la base d’un autre module ;
- un appel externe passe par un port puis un adaptateur ;
- l’état métier et l’événement outbox sont atomiques ;
- les événements entrants passent par une inbox idempotente ;
- les références externes et les prix nécessaires à l’historique sont
  conservés comme snapshots ;
- DiddiMap n’est pas une dépendance DiddiShop.

## Modules internes

| Module | Responsabilité |
| --- | --- |
| `shops` | boutiques, membres et règles de propriété vendeur |
| `catalog` | produits, publication, médias référencés et stock |
| `cart` | panier acheteur et lignes regroupées |
| `checkout` | validation du panier, snapshot financier et orchestration initiale |
| `orders` | commande, transitions, historique et projection logistique |
| `delivery` | port DiddiSend et projection de livraison |
| `claims` | annulations, réclamations et décisions |
| `finance` | refunds et règles financières V1 |
| `rewards` / `campaigns` | avantages et projection de campagnes DiddiRewards |
| `comms` | accès au parcours conversation métier |
| `support` | contexte, cas support et actions idempotentes |
| `observability` | conventions de télémétrie et exposition interne |
| `admin` / `audit` | commandes backoffice et traçabilité opérateur |
| `workers` | outbox, inbox et événements entrants |

## Possession des données externes

| Donnée | Source de vérité | DiddiShop conserve |
| --- | --- | --- |
| Produit, stock, prix de commande | DiddiShop | état et snapshot |
| PaymentIntent et refund | DiddiPay | références, statuts et réconciliation |
| Livraison et coursier | DiddiSend | `delivery_id`, statut projeté et preuve référencée |
| Binaire et URLs de fichier | DiddiFiles | `file_id`, purpose et metadata utile |
| Campagne, benefit, ledger | DiddiRewards | quote/réservation et snapshot |
| Conversation | DiddiComms | référence et lien métier |
| Cas support | DiddiSupport | référence et timeline utile |
| Traces/logs/metrics | DiddiObserve | aucun état métier |
| Identité et tokens | DiddiFreeID | principal et contexte d’autorisation |

## Exécution locale

Le `docker-compose.local.yml` démarre PostgreSQL, Redis et l’API en mode
`development`. Les repositories de développement utilisent encore les
implémentations locales prévues par le squelette ; `/ready` vérifie néanmoins
les connexions réelles PostgreSQL/Redis et Alembic applique les migrations
réelles. Ce Compose ne contient aucun secret ni appel financier réel.
