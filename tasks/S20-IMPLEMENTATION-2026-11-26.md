# S20 — journal d’implémentation

- Audit de `app.openapi()` : 39 chemins métier montés.
- Aucun décorateur WebSocket ni protocole `ws://`/`wss://` trouvé.
- Les protocoles REST/JSON, webhooks signés, S2S Bearer/client credentials et
  OTLP HTTP/protobuf sont désormais regroupés dans une page MkDocs dédiée.
- Les réponses génériques non encore typées sont signalées explicitement.
- MkDocs strict doit être exécuté avant livraison.
