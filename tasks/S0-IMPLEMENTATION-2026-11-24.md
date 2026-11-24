# Journal S0 — 2026-11-24

## S0-A — frontière DiddiMap

- Suppression de l’adaptateur `DiddiMapAdapter`.
- Suppression de `diddimap_base_url` et de l’entrée du registre d’intégrations.
- Documentation et décision D-016 alignées sur DiddiSend comme propriétaire de
  la validation opérationnelle de livraison.

## S0-B — configuration staging

- Ajout des URLs HTTPS et de l’endpoint S3 dans `.env.example`.
- Ajout d’un contrôle fail-closed pour les environnements non développement.
- Les secrets restent injectés par le gestionnaire de secrets.

## S0-C — runtime et vérification

- `app.state.outbox` est créé avant les services qui le consomment.
- Tests de configuration ajoutés.
- Vérifications : `22 passed`, compilation OK, Ruff OK.

## Déploiement en attente

- Fournir les credentials S2S réels.
- Confirmer le contrat DiddiFiles `diddishop_product_image`.
