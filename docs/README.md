# Documentation DiddiShop

Cette documentation est la référence humaine du backend DiddiShop. Elle suit
la convention documentaire de DiddiGo : le contrat API décrit la surface
exposée, les guides décrivent les parcours, les pages d’intégration décrivent
les frontières externes et les références regroupent les états et la
configuration.

## Navigation

- Contrat HTTP et webhooks : [`api/API_CONTRACT.md`](api/API_CONTRACT.md)
- Référence détaillée des routes : [`api/ROUTE_REFERENCE.md`](api/ROUTE_REFERENCE.md)
- Questions et contrats à valider : [`api/open-questions.md`](api/open-questions.md)
- Architecture d’exécution : [`architecture/RUNTIME_ARCHITECTURE.md`](architecture/RUNTIME_ARCHITECTURE.md)
- MVP figé : [`product/DIDDISHOP-MVP-FIGE.md`](product/DIDDISHOP-MVP-FIGE.md)
- Parcours checkout/commande : [`guides/checkout-order-flow.md`](guides/checkout-order-flow.md)
- Parcours annulation/réclamation : [`guides/claims-refunds-flow.md`](guides/claims-refunds-flow.md)
- Intégrations : DiddiSend, DiddiPay, DiddiFiles, DiddiRewards, DiddiComms,
  DiddiSupport, DiddiObserve et DiddiFreeID dans le menu ci-dessous
- États et transitions : [`reference/statuses.md`](reference/statuses.md)
- Configuration : [`reference/configuration.md`](reference/configuration.md)
- Journal des changements : [`changelog/2026-11-25.md`](changelog/2026-11-25.md)
- Runbook opérationnel : [`operations/runbook.md`](operations/runbook.md)
- Publication web : [`operations/documentation-portal.md`](operations/documentation-portal.md)

## Source du contrat

La surface HTTP runtime est générée par FastAPI et disponible sur
`/openapi.json`. Le contrat humain de ce dépôt explique les garanties métier
et les frontières ; il ne remplace pas les schémas runtime lorsque ceux-ci
évoluent. Toute modification de route, de webhook ou de schéma doit mettre à
jour le contrat, le guide concerné et le changelog du jour.

Les fichiers `CAPABILITY-MAP.md`, `INTEGRATION_MAP.md` et
`ARCHITECTURE_SKELETON.md` restent les cartes de conception détaillées. Les
documents dans `tasks/` décrivent l’historique d’implémentation et ne sont pas
la référence d’intégration publique.

## Règles de maintenance

- Ne jamais documenter DiddiMap comme une dépendance DiddiShop.
- DiddiSend est l’unique frontière logistique.
- Tous les montants métier sont en XOF dans la V1.
- La séquestration et la release vendeur DiddiPay restent V2.
- Un contrat externe non vérifié doit être marqué `À valider`, jamais inventé.
- Les secrets, tokens et valeurs privées ne doivent apparaître ni dans les
  exemples ni dans les commits.
