# S19 — journal d’implémentation

## Réalisation

- `POST /v1/orders/{order_id}/ready` utilise désormais le service livraison.
- Une commande `TO_PREPARE` devient `READY_FOR_PICKUP`, puis DiddiShop appelle
  DiddiSend avec la clé stable `shop:create-delivery:{order_id}:1`.
- Une commande déjà prête est rejouable ; une projection existante empêche une
  deuxième création de livraison.
- MkDocs précise que le frontend vendeur ne contacte jamais DiddiSend
  directement.

## Vérification

- Test ajouté pour le déclenchement et le rejeu sans duplication.
- Vérifications complètes à exécuter avant commit.
