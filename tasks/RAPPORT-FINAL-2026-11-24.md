# DiddiShop — rapport final d’implémentation

**Date :** 2026-11-24  
**Statut :** implémentation locale complète ; recette staging en attente

## Phases terminées

S0 à S10 sont terminées localement : frontières et configuration, PostgreSQL/
Redis, identité et scopes, DiddiFiles, catalogue, checkout, DiddiPay,
DiddiSend, finance, Rewards, Comms, Support, Observe et DiddiBackoffice.
DiddiMap est hors périmètre ; DiddiSend est l’unique propriétaire de
l’expédition. Les tokens S2S utilisent maintenant `client_credentials` avec un
client DiddiFreeID distinct par service cible.

## Commits poussés sur `main`

```text
d5b0795 feat(s0): align staging boundaries and configuration
98024e4 feat(s1): add durable persistence and event workers
6c8ec0e feat(s2): enforce jwt scopes and webhook signatures
7d2796f feat(s3): integrate diddifiles and persistent catalog
47db843 feat(s4): persist payment references and order orchestration
1442acd feat(s5): align prepaid delivery with diddisend
42abcdf feat(s6): harden claims refunds and delivery failures
10152dc feat(s7): wire rewards communications support and observe
f54c115 feat(s8): secure backoffice and readiness checks
aaf37f3 feat(s2s): add per-service client credentials tokens
233dae6 fix(comms): separate conversations from notifications
```

## Vérifications locales

- `pytest -q` : 43 tests passés ;
- `ruff check .` : OK ;
- `python -m compileall -q app_base tests alembic` : OK ;
- `alembic upgrade head --sql` : OK ;
- `git diff --check` : OK.

## Bloqué ou en attente de recette

- PostgreSQL et Redis réels, migrations et workers staging ;
- credentials/scopes S2S DiddiFreeID ;
- contrat DiddiSend pour prépaiement et ventilation XAF, le schéma observé
  étant Food/XOF ;
- visibilité des images DiddiFiles ;
- enveloppes finales Comms/Support ;
- rétablissement et validation de DiddiObserve, observé en `502` ;
- tests end-to-end staging et alertes opérationnelles.

La séquestration des fonds et la release vendeur ne sont pas des éléments
bloquants du MVP : elles sont explicitement reportées en V2.

Ces points sont documentés dans `docs/IMPLEMENTATION-STATUS.md` et
`docs/CONTRACTS-TO-VALIDATE.md`. Aucun fallback financier silencieux n’a été
introduit.
