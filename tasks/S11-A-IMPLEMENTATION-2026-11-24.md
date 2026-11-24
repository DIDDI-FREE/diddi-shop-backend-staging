# S11-A — journal d'implémentation

- Statut : terminé
- Quote, reserve, confirm, release et correct utilisent le préfixe
  `/internal/v1/rewards/integrations/diddishop` ; les écritures portent
  `Idempotency-Key`.
- Le snapshot conserve `campaign_id`, `campaign_version_id`, `entitlement_id`,
  la remise, le montant final et la devise.
- Déploiement à vérifier : client S2S Shop, scopes quote/reserve/consume/correct
  et audience staging.
