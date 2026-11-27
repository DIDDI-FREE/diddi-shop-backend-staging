# Rapport — correctifs paiement S24-O et S24-P

- S24-O terminé : `751b1c93e0a6a16111c4481b261cb0ebceab35b4`.
  `return_url` → `callback_url`, conservation/reprise historique, alternative
  `return_target`, `next_action` frontend et page neutre `/payments/return`.
- Choix délégué D-057 : retour par défaut sur le backend HTTPS DiddiShop,
  configurable, suivant le principe des autres modules ; aucun secret nouveau.
- D-058 (Agent, à valider) : corps retry facultatif/idempotent, actions de paiement
  typées et quatre refus Pay de destination traités explicitement comme échec.
- Tests : 133 réussis sur hôte et Docker Desktop Python 3.12 sans réseau ;
  Ruff Windows/Linux, compilation, MkDocs strict, Alembic SQL, deux Compose OK.
- Aucun sous-lot de ce correctif bloqué ; aucune branche WIP. Les réserves
  de recette des phases précédentes restent dans `docs/IMPLEMENTATION-STATUS.md`.
- À valider avec Pay : acceptation du callback de retour selon sa configuration,
  ou enregistrement d'un target Shop. Aucun target provisionné n'est supposé.
- Non testé : paiement PawaPay réel, ouverture d'une vraie session fournisseur,
  boucle webhook/retour staging. Les mocks ne prouvent pas ce résultat.
- Déploiement Git manuel par l'utilisateur seulement, puis retry avec nouvelle
  clé sur checkout failed et vérification `Idempotency-Replayed=false`.
- Aucun autre dépôt modifié ; aucun secret commité ; aucune mutation Portainer.

Réalisations antérieures : rapport du 24 novembre et journaux S24-A à S24-N.

## S24-P — sauvegarde webhook et parcours vendeur/livraison

- Terminé : `a7a78688bd58afd66706dc8b85bbcd3397c0f4be`.
- Cause : enums non restaurés après JSON et modifications paiement/Rewards
  perdues lors d'un rechargement. Correction des lectures ShopService.get et
  de la sauvegarde de livraison avec une instance obsolète.
- 238 tests hôte et Docker sans réseau, plus un parcours complet avec HMAC et
  PostgreSQL 16 Docker réel : succès → vendeur → livraison simulée jusqu'à
  DELIVERED. Lint hôte/Linux, compilation, MkDocs strict et Alembic SQL OK.
- Base synthétique et réseau de test supprimés ; aucun volume de staging touché.
- Décision D-059 documentée ; D-060 Agent à valider. Pas de sous-lot bloqué,
  aucun nouveau contrat fournisseur ou changement de schéma requis.
- Après déploiement Git manuel utilisateur : faire reprendre le callback original
  par DiddiPay et vérifier checkout `payment_succeeded`, commande `TO_CONFIRM`.
  **Ne pas relancer le paiement** pour réparer sa notification de succès.
- Non testé : reprise du webhook réel en staging, concurrence distribuée et
  appel DiddiSend réel dans ce parcours. Aucun autre backend ni Portainer modifié.
