# S17 — Journal d’implémentation

## S17-A/B — Middleware et tests

- Ajout de `CORSMiddleware` dans `app_base/main.py`.
- Origines autorisées : HTTP/HTTPS des sous-domaines `*.diddifree.com` et
  `localhost` avec port optionnel.
- Méthodes et headers nécessaires au frontend autorisés, dont `Authorization`.
- Credentials navigateur désactivés ; l’authentification frontend repose sur
  Bearer JWT.
- Tests ajoutés dans `tests/test_cors.py`.

## S17-C — Vérification

- `ruff check .` : OK.
- `pytest -q` : 60 tests passés.
- `python -m compileall -q app_base` : OK.
- `git diff --check` : OK.
- Image API et documentation reconstruites localement.
- Préflight Docker local : 200 pour DiddiFree/localhost, origine arbitraire
  refusée.

## Déploiement en attente

- Redéployer l’image API depuis ce commit dans Portainer.
- Vérifier ensuite le préflight sur `https://diddishop-backend.diddifree.com`.
