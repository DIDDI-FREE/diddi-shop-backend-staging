# DiddiShop

Squelette backend du marketplace physique DiddiShop.

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
