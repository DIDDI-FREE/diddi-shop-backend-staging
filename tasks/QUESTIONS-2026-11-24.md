# Questions bloquantes avant la boucle autonome — réponses intégrées

Les réponses utilisateur ont été intégrées le 2026-11-24. Q1 est traité par
une décision prudente d’agent, à valider dans `DECISIONS.md`.

## Q1 — Release vendeur DiddiPay

**Contexte :** le plan exige une libération après 72 h, mais le contrat observé
de DiddiPay ne formalise pas encore clairement l’allocation marketplace/hold/release.

- **Option A — recommandée :** avancer avec `SellerReleasePort`, faux adaptateur
  testé et état `RELEASE_PENDING`, puis brancher l’endpoint DiddiPay quand validé.
- Option B : bloquer toute la finance et attendre le contrat DiddiPay avant de
  coder P5.

**Réponse :** Agent — port abstrait et faux adaptateur, contrat réel à valider.

## Q2 — Livraison prépayée DiddiSend

**Contexte :** DiddiShop possède déjà le checkout et le paiement ; DiddiSend
doit créer la livraison sans créer un second PaymentIntent.

- **Option A — recommandée :** définir un contrat `prepaid_by_origin=true` avec
  `origin_service=diddishop`, le coder derrière un port et marquer l’appel réel
  à valider.
- Option B : DiddiSend reste propriétaire du paiement de livraison, avec un
  mécanisme de transfert explicite entre les services.

**Réponse :** imiter le modèle DiddiFood, avec `origin_module=diddishop` et un
payload DiddiSend complet.

## Q3 — Base et infrastructure locale

**Contexte :** le plan demande PostgreSQL, migrations et workers ; le squelette
actuel ne configure ni PostgreSQL ni Redis.

- **Option A — recommandée :** PostgreSQL + SQLAlchemy async/Alembic et Redis
  pour outbox/inbox/locks, SQLite réservé aux tests unitaires.
- Option B : PostgreSQL seul avec polling SQL de l’outbox, sans Redis au MVP.
- Option C : rester en mémoire jusqu’à l’intégration staging.

**Réponse :** PostgreSQL + Redis.

## Q4 — Authentification S2S DiddiFreeID

**Contexte :** il faut provisionner l’audience et les scopes du client
`diddishop`, mais les valeurs exactes ne sont pas encore dans le dépôt Shop.

- **Option A — recommandée :** appliquer des scopes dédiés et minimaux par
  service (`diddipay:*`, `diddisend:*`, `diddifiles:*`, etc.) derrière une
  configuration d’environnement, sans fallback par clé globale.
- Option B : utiliser temporairement les clés S2S legacy existantes.

**Réponse :** oui, scopes dédiés par service.

## Q5 — Dépôt Git et push

**Contexte :** `E:\DIDDI AI\diddi-shop` n’est pas un dépôt Git ; la mission exige
un commit dédié par sous-lot et un push.

- **Option A — recommandée :** tu fournis/initialises le dépôt distant et la
  branche ; je poursuis ensuite avec commits et push.
- Option B : j’initialise un dépôt Git local sans push distant ; les commits
  restent locaux.
- Option C : je poursuis sans commits/push et je journalise cette impossibilité.

**Réponse :** initialiser le dépôt Git et utiliser le remote fourni.
