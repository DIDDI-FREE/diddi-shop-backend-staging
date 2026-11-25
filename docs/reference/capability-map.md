# Carte des capacités

Cette page résume la carte de conception complète du dépôt, conservée dans le
fichier `CAPABILITY-MAP.md` à la racine.

```text
platform-runtime
        ↓
observability → identity-access → external-integrations
                                      ↓
                         shops → catalog → cart
                                      ↓
                              checkout → orders
                                      ↓
                                  claims / finance
                                      ↓
                         rewards / comms / support / admin
```

Chaque module possède ses règles et ses ports. Les données d’un autre module
ne sont pas lues directement ; les échanges passent par use case, port ou
événement.
