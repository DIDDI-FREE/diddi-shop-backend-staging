# DiddiShop

Squelette backend du marketplace physique DiddiShop.

## Documentation active

La documentation suit la convention de DiddiGo :

- [Portail documentaire](docs/README.md)
- [Contrat HTTP et webhooks](docs/api/API_CONTRACT.md)
- [Architecture d’exécution](docs/architecture/RUNTIME_ARCHITECTURE.md)
- [MVP V1 figé](docs/product/DIDDISHOP-MVP-FIGE.md)
- [Parcours checkout/commande](docs/guides/checkout-order-flow.md)
- [Intégrations externes](docs/integrations/)
- [Questions ouvertes](docs/api/open-questions.md)

Pour prévisualiser le portail comme DiddiGo :

```powershell
python -m pip install -r docs/requirements.txt
mkdocs serve
```

Le découpage reprend une composition Clean Architecture :

- `domain` contient les règles métier et les ports (`Protocol`) ;
- `application` orchestre les cas d’usage ;
- `infra` implémente la persistance et les adaptateurs ;
- `presentation` expose les routes ;
- `core/deps.py` compose les dépendances et les ressources `app.state` ;
- `shared_kernel/contracts` contient uniquement les contrats stables et versionnés.

## Démarrage du squelette

```powershell
python -m pip install -e ".[dev]"
uvicorn app_base.main:app --reload
```

## Vérification locale avec Docker

Le Compose local démarre PostgreSQL, Redis et l’API en mode développement :

```powershell
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build
docker compose ps
Invoke-WebRequest http://localhost:18080/health
Invoke-WebRequest http://localhost:18080/ready
docker compose -f docker-compose.yml -f docker-compose.local.yml down
```

Le portail documentaire public est une stack séparée :

```powershell
docker compose -f docker-compose.docs.yml -f docker-compose.docs.local.yml up -d --build
Invoke-WebRequest http://localhost:18082/
```

En staging, le Proxy Host doit publier le conteneur docs sur
`https://docs-diddishop-staging.diddifree.com/`. Le frontend ne doit pas lire
les fichiers depuis Git ou le poste de développement.

En staging, utiliser l’overlay réseau sans aucun `ports:` hôte :

```powershell
$env:NPM_NETWORK = "<nom-exact-du-reseau-partage-avec-NPM>"
docker compose -f docker-compose.yml -f docker-compose.docs.yml -f docker-compose.proxy.yml up -d --build
```

Nginx Proxy Manager doit cibler `api:8000` pour l’API et `docs:80` pour la
documentation. Le nom réel du réseau doit être fourni par l’hôte NPM ; il ne
peut pas être déduit depuis ce poste si NPM tourne sur une autre machine.

Il ne contient aucun credential métier et n’exécute aucun paiement ou envoi
réel. Les contrats externes sont vérifiés par les tests avec faux services HTTP
et doivent être rejoués en staging avec les secrets provisionnés.

Le code livré ici est un squelette de frontières et de contrats. Les repositories
et adaptateurs externes sont volontairement des points d'extension ; ils ne
simulent pas encore un paiement, une livraison ou un remboursement réel.

## Flux de dépendances

```text
HTTP / workers
     |
presentation -> application -> domain ports
                              ^
                              |
                 infra repositories + integrations

integrations -> DiddiPay / DiddiSend / DiddiFiles / DiddiRewards
              DiddiComms / DiddiSupport / DiddiObserve / DiddiFreeID
```

Un module métier ne doit jamais importer directement le repository ou le client
HTTP d’un autre module. Il dépend d’un port local ou d’un événement.
