# S22 — Journal d’implémentation

## S22-A

- Panier enrichi avec titre, prix, total de ligne et sous-totaux boutique.
- Commandes enrichies avec lignes financières, `created_at`, échéance vendeur
  et adresse de livraison.
- Livraison enrichie avec coursier, position et code de remise.
- Annulation avec `OrderResponse` et codes `ORDER_NOT_CANCELLABLE`/
  `DELIVERY_ALREADY_PICKED_UP`.

## S22-B

- `POST /v1/checkouts/quote` ajouté sans création de paiement.
- `GET /v1/checkouts/{checkout_id}` ajouté pour le suivi du paiement.
- `POST /v1/checkouts/{checkout_id}/retry` ajouté pour un paiement échoué.
- Création et reprise protégées par l’idempotence persistante configurée dans
  l’application.
- Adresse physique et téléphone E.164 requis pour une commande physique.

## S22-C

- Pause/retrait produit ajoutés.
- Maximum de huit photos et formats JPEG/PNG/WebP, taille maximale 10 MiB.
- MkDocs et les contrats API alignés sur le code réel.

## Vérification

- `ruff check .` : OK.
- `pytest -q` : 69 passed, 1 warning de dépréciation Starlette/httpx.
- Vérification staging et credentials externes : en attente du redéploiement.
