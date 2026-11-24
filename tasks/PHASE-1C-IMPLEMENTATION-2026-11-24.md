# PHASE 1C — contexte HTTP et sécurité de base

**Statut :** terminé

Le middleware ajoute `X-Request-ID` et `X-Correlation-ID`. Les scopes S2S sont
déclarés par service et les headers sortants incluent l’origine, l’acteur, la
credential, la corrélation et la clé d’idempotence.

La validation JWKS DiddiFreeID complète reste dans le sous-lot d’identité de la
phase suivante ; aucun token n’est accepté implicitement par le domaine.
