# S24-O — retour navigateur Payment Page

## Cause établie

Le modèle Shop acceptait `return_url` mais l'adaptateur ne l'envoyait pas à Pay.
L'option n'était pas sauvegardée dans le paiement, alors que le retry la lisait
à cet endroit. Deux tests rouges reproduisaient l'absence de `callback_url` et
l'impossibilité de restituer la redirection Payment Page.

OpenAPI DiddiPay staging lu par GET : `return_target`, `callback_url` déprécié
et `next_action` sont présents. Resolver, schéma et PawaPay lus dans DiddiPay,
sans modification. Retour navigateur DiddiSend/DiddiGo/DiddiFood observé en
lecture seule. Aucun chemin callback fournisseur n'a été utilisé comme retour.

## Implémentation

- Destination explicite, sinon valeur backend HTTPS choisie sur délégation
  utilisateur : `https://diddishop-backend.diddifree.com/payments/return`.
- Page neutre réellement implémentée, sans lecture/écriture métier, sans
  réflexion des paramètres ni redirection libre ; CSP et no-store.
- Mapping `return_url` → `callback_url`, alternative `return_target`, exclusifs.
  Validation avant effets. Entrées conservées même si Pay renvoie null.
- Retry : option du corps, paiement enregistré, commande historique, défaut
  configurable. Le hash d'idempotence inclut les nouvelles options tout en
  conservant les hashes historiques lorsque ces options sont absentes.
- `next_action` structurée et `payment_url` de redirection transmis au frontend.
- Quatre refus de configuration Pay 422 connus deviennent des échecs explicites
  retryables ; aucun intent inventé. Pas de normalisation hasardeuse des timeouts
  ou 5xx. État pending sauvegardé sans garder l'ancien `status=failed` lors d'une
  nouvelle tentative, pour éviter une réconciliation fausse avant son résultat.
- Handler de validation : sérialisation des ValueError Pydantic pour renvoyer
  un vrai 422, pas une erreur JSON 500.
- Compose, templates non secrets, OpenAPI, MkDocs, décisions D-057/D-058.
  Aucune migration nécessaire. Aucun fichier hors dépôt modifié.

## Vérifications

- Suite locale : 133 passed (27 cas supplémentaires), 2 dépréciations existantes.
- Ruff, compilation Python, MkDocs strict, Alembic génération SQL : OK.
- Deux Compose validés par `config --quiet` avec exemples non sensibles : OK.
- Docker Desktop Python 3.12 : image `diddishop-return-tests:local`,
  `docker run --rm --network none` : 133 passed ; Ruff Linux OK.
  Contexte de build autorisé explicitement, aucun secret embarqué.
- Tests routes réelles + repositories SQL SQLite + port/adaptateur réel + HTTP
  simulé, couvrant nouveaux/historiques, absence/destination invalide, rejet Pay,
  idempotence, redirection, settings et réponse HTML sans effet financier.

## Limites / recette manuelle

La réussite du fournisseur et son autorisation de retour ne sont pas déduites
des mocks. Aucun prélèvement réel, aucun déploiement ou redéploiement Portainer.
Vérifications à effectuer par l'utilisateur après déploiement Git : section
S24-O de `docs/IMPLEMENTATION-STATUS.md`. Aucun target Shop supposé provisionné.
La règle Diddi Portainer Ops a imposé le suivi documentaire et le contrôle des
Compose ; elle n'a autorisé aucune mutation distante.
