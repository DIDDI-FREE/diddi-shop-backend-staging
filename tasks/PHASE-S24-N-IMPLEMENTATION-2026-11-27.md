# S24-N — téléphone PaymentIntent et idempotence

## Constats et limites

- Portainer lu uniquement : stack Git `diddishop-backend`, référence main,
  ConfigHash `608461354d4a14083ca4b078208ea06ecd747c98` au moment de la lecture.
  Ce champ identifie la référence de stack, pas une preuve du code chargé.
- Le log Shop contient un retry HTTP 200 à 03:28:56 UTC. Les lectures de logs
  Pay ne permettent pas d'établir à elles seules la cause exacte de cet essai
  (une lecture ultérieure ne retrouvait plus l'ancien conteneur).
- Tests avant correction : 11 échecs / 1 succès. Téléphone nullable écrasant
  l'entrée, valeurs historiques invalides acceptées, aucun blocage avant appel,
  absence d'indicateur de réponse rejouée. Un échec intermédiaire de collecte
  venait d'un patch incomplet, corrigé sans affaiblir les assertions.

## Changements

- Téléphone E.164 obligatoire jusqu'au JSON HTTP DiddiPay ; `recipient_phone`
  est traduit en `customer_phone`. Le port ne peut plus ignorer les options.
- Retry historique : première valeur valide du paiement ou des commandes ;
  sinon 422 avant effets. Aucun numéro inventé et aucune modification DiddiPay.
- Préservation du téléphone validé malgré un écho fournisseur nul.
- Réhydratation de CheckoutStatus après SQL pour GET/retry.
- Header de rejeu documenté OpenAPI/MkDocs et accessible par CORS. La même clé
  restitue le même résultat, nouvelle clé après échec = nouvelle tentative.
- Logs de rejeu/appel/résultat sans téléphone, secret ou clé d'idempotence.

## Vérifications

- `python -m pytest -q` : 106 passed (deux avertissements de dépréciation).
- `python -m ruff check .` : OK.
- `python -m compileall -q app_base tests alembic` : OK.
- `python -m mkdocs build --strict` : OK.
- `python -m alembic upgrade head --sql` : OK ; schéma inchangé.
- Docker Desktop local : image de tests Python 3.12, `docker run --rm
  --network none diddishop-phone-tests:local` : 106 passed.
- Lint Linux : fichiers Python copiés depuis Windows avec bit exécutable ;
  permissions normalisées à 0644 dans l'image de tests, sans désactiver EXE002.
- Tests intégrés : routes HTTP, vrais repositories SQL (SQLite en mémoire),
  vrai port/adaptateur DiddiPay, MockTransport. Aucun appel PawaPay réel.
- Décisions D-055 et D-056. Graphify consulté comme carte d'orientation ;
  preuves établies par le code actuel et les tests, pas par le graphe ancien.

## À vérifier après déploiement manuel

- Rejeu d'une ancienne clé : header true, aucun paiement supplémentaire.
- Nouvelle tentative autorisée : header false, compteur incrémenté,
  événements corrélables côté Shop/Pay et absence de rejet pour téléphone absent.
- Pas de revendication de succès de paiement réel sur la base des mocks.
