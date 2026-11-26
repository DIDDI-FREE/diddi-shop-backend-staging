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

Le Compose local démarre PostgreSQL, Redis, l’API et le portail MkDocs dans
la même stack :

```powershell
docker compose -f docker-compose.local.yml up -d --build
docker compose -f docker-compose.local.yml ps
Invoke-WebRequest http://localhost:48180/health
Invoke-WebRequest http://localhost:48180/ready
Invoke-WebRequest http://localhost:48182/
docker compose -f docker-compose.local.yml down
```

Pour démarrer uniquement le portail documentaire :

```powershell
docker compose -f docker-compose.docs.yml up -d --build
Invoke-WebRequest http://localhost:48182/
```

Pour reproduire le déploiement Portainer de DiddiGo, utiliser
`docker-compose.yml`. Cette stack construit l’API et MkDocs depuis
la même révision Git, puis expose les ports hôte configurables `48180` et
`48182` pour Nginx Proxy Manager. Voir
[`docs/operations/documentation-portal.md`](docs/operations/documentation-portal.md)
pour les variables Portainer et le Proxy Host HTTPS.

Le modèle des variables à charger dans Portainer est
`portainer.env.example`. Le fichier opérationnel `portainer.env` reste local,
ignoré par Git, et doit recevoir les secrets provisionnés avant déploiement.

En staging, le Proxy Host doit publier le conteneur docs sur
`https://docs-diddishop-staging.diddifree.com/`. Le frontend ne doit pas lire
les fichiers depuis Git ou le poste de développement.

En staging, la configuration par défaut publie des ports hôte élevés et
configurables : `48180` pour l’API et `48182` pour la documentation. Si le
réseau NPM est finalement accessible, l’overlay réseau reste disponible :

```powershell
$env:NPM_NETWORK = "<nom-exact-du-reseau-partage-avec-NPM>"
docker compose --env-file portainer.env -f docker-compose.yml -f docker-compose.proxy.yml up -d --build
```

Sans réseau Docker partagé, Nginx Proxy Manager doit cibler le host Docker et
les ports `48180` et `48182`. Avec le réseau partagé, il peut cibler `api:8000`
et `docs:80`. Le nom réel du réseau doit être fourni par l’hôte NPM ; il ne
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
