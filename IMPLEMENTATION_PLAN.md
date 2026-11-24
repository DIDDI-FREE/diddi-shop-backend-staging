# DiddiShop — plan d’implémentation du MVP

**Version :** 0.1 — 24 novembre 2026  
**Base :** `DiddiShop — Specs backend du MVP v1.1 — cadrage.md` et
`CAPABILITY-MAP.md`  
**Statut :** MVP V1 cadré ; séquestration/release vendeur reportées en V2

## 1. Décision d’architecture

DiddiShop est un monolithe modulaire Clean Architecture au départ. Les modules
sont séparés par des ports, des use cases, des événements et des repositories.
Ils peuvent être extraits plus tard sans réécrire le domaine.

La seule dépendance d’expédition de DiddiShop est DiddiSend :

```text
DiddiShop -> DiddiSend -> livraison
```

DiddiShop ne lit aucune base de flotte, ne connaît pas les coursiers et
n’appelle aucun endpoint de flotte. Toute orchestration interne à DiddiSend
reste dans DiddiSend.

## 2. Périmètre d’implémentation

### Inclus dans le MVP

- boutique vendeur et statut de boutique ;
- catalogue de produits physiques, photos, prix, catégories et stock ;
- panier multi-boutiques sans réservation de stock ;
- checkout avec snapshot des prix, frais et paramètres financiers ;
- un paiement DiddiPay par checkout ;
- une commande DiddiShop par boutique ;
- confirmation vendeur sous 24 heures ;
- devis et création d’expédition DiddiSend ;
- suivi des étapes de livraison ;
- annulation avant prise en charge ;
- livraison échouée et retour ;
- réclamation acheteur dans les 72 heures après livraison ;
- remboursement total ou partiel selon décision ;
- libération vendeur après 72 heures sans réclamation ;
- notifications via DiddiComms ;
- contexte et décision support via DiddiSupport ;
- observabilité et audit ;
- lecture et commandes limitées via DiddiBackoffice ;
- intégration DiddiRewards limitée à l’application de bénéfices et à la
  consommation des campagnes publiées.

La séquestration des fonds et la release vendeur ne font pas partie du MVP V1.
Le paiement est confirmé et remboursable via DiddiPay ; aucun payout vendeur
ou mécanisme de hold marketplace n’est déclenché par DiddiShop.

### Hors périmètre de DiddiShop pour ce MVP

- moteur de campagnes, budget, ledger et règles de récompenses : propriété de
  DiddiRewards ;
- paiement à la livraison ;
- produits digitaux ;
- variantes de produits ;
- livraison partielle ;
- coupons/promotion engine local ;
- avis, recommandations et scoring ;
- portefeuille et retrait vendeur ;
- gestion de flotte/coursiers ;
- interface opérateur complète : propriété de DiddiBackoffice.

## 3. Ordre de construction

```text
P0 Fondations
   ↓
P1 Identité + intégrations + observabilité
   ↓
P2 Boutiques + catalogue + médias + stock
   ↓
P3 Panier + checkout + commandes
   ↓
P4 Paiement confirmé + expédition DiddiSend
   ↓
P5 Annulations + retours + réclamations + remboursements
   ↓
P6 Rewards/campagnes + communication + support
   ↓
P7 Backoffice + durcissement + recette MVP
```

`observability`, `audit`, `outbox/inbox` et l’idempotence sont transverses à
toutes les phases. Ils ne sont pas repoussés à la fin.

## 4. Plan par phase

### P0 — Fondations techniques

**Objectif :** rendre le squelette exécutable et transactionnel.

À implémenter :

- PostgreSQL, migrations et session transactionnelle ;
- configuration par environnement ;
- horloge et générateurs d’identifiants injectables ;
- tables `outbox_events`, `inbox_events`, `idempotency_records` et audit ;
- middleware `request_id`, `correlation_id` et `traceparent` ;
- gestion d’erreurs API uniforme ;
- worker outbox avec retry/backoff et dead-letter ;
- verrouillage optimiste ou `SELECT ... FOR UPDATE` pour les agrégats sensibles.

**Acceptation :** une transition métier et son événement outbox sont validés
dans la même transaction ; un retry de worker ne publie pas deux effets métier.

**Tests :** migrations propres, rollback transactionnel, retry outbox, doublon
inbox, conflit de clé d’idempotence.

### P1 — Identité, sécurité et adaptateurs externes

**Objectif :** brancher les services sans faire entrer HTTP ou JWT dans le domaine.

À implémenter :

- validation JWT utilisateur et contexte S2S via DiddiFreeID ;
- permissions vendeur par boutique ;
- `PaymentPort` vers DiddiPay ;
- `DeliveryPort` vers DiddiSend ;
- `FilePort` vers DiddiFiles ;
- `RewardsPort` vers DiddiRewards ;
- `CommunicationPort` vers DiddiComms ;
- `SupportPort` vers DiddiSupport ;
- export télémétrie vers DiddiObserve ;
- validation opérationnelle des adresses par DiddiSend dans le contrat de livraison ;
- timeout, retry borné, circuit-breaker ou état `processing` pour chaque appel.

**Acceptation :** aucun use case ne construit une URL HTTP et aucun module ne
connaît les secrets ou tokens d’un autre service.

**Tests :** tests contractuels avec clients mockés, signature/authentification,
timeouts, erreurs 4xx/5xx, reprise après réponse inconnue.

**Bloquants à obtenir avant activation réelle :**

1. contrat DiddiSend pour créer une livraison déjà payée par DiddiShop ;
2. visibilité/URL signée du purpose `diddishop_product_image` dans DiddiFiles ;
3. scopes S2S DiddiShop dans DiddiFreeID.

Le contrat marketplace DiddiPay de hold/release est explicitement hors V1 et
sera traité dans le périmètre V2.

### P2 — Boutiques, catalogue, médias et stock

**Objectif :** permettre au vendeur de publier un produit physique achetable.

À implémenter :

- `shops` : création, mise à jour, suspension, adresse de retrait ;
- `catalog` : produit, catégorie, prix XAF, statut de publication ;
- références `file_id` et validation du purpose via DiddiFiles ;
- lecture publique du catalogue ;
- stock disponible et décrément atomique ;
- restitution de stock idempotente après annulation avant expédition ;
- snapshot du titre, prix, commission et référence média à la commande.

**Acceptation :** deux validations concurrentes ne peuvent pas vendre le même
dernier article ; le prix de la commande ne change jamais si le catalogue est
modifié ensuite.

**Tests :** droits vendeur, publication, stock à zéro, concurrence, restitution
unique, média invalide, boutique suspendue.

### P3 — Panier, checkout et commandes

**Objectif :** transformer un panier multi-boutiques en commandes cohérentes.

À implémenter :

- panier par acheteur et regroupement par `shop_id` ;
- contrôle disponibilité et calcul des frais DiddiSend ;
- réservation logique Rewards avant paiement si un bénéfice est applicable ;
- décrément atomique du stock à la validation ;
- création d’un checkout et d’une commande par boutique ;
- snapshot financier par commande ;
- création d’un PaymentIntent DiddiPay avec clé stable ;
- machine d’états de `orders` ;
- historique append-only des transitions ;
- événements `order.created`, `order.confirmed`, `order.cancelled` et
  `order.ready_for_pickup`.

**Acceptation :** un panier de trois boutiques crée trois commandes reliées à
un checkout ; un paiement confirmé fait passer uniquement ces commandes à
`TO_CONFIRM` ; un échec annule et restitue le stock une seule fois.

**Tests :** double validation, webhook avant réponse de création, paiement
dupliqué, vendeur et annulation concurrents, panier multi-boutiques.

### P4 — Paiement confirmé et expédition DiddiSend

**Objectif :** exécuter le parcours physique sans coupler Shop à la flotte.

À implémenter :

- webhook DiddiPay authentifié et dédoublonné ;
- mapping `payment.succeeded` → paiement `HELD` et commande `TO_CONFIRM` ;
- confirmation vendeur → `TO_PREPARE` ;
- vendeur marque le colis prêt ;
- création DiddiSend avec `origin_service=diddishop` et référence de commande ;
- persistance de `delivery_id` et du devis figé ;
- consommation des événements `delivery.*` ;
- mapping vers `PICKED_UP`, `IN_TRANSIT`, `DELIVERED`, `RETURNED`, `FAILED` ;
- preuve de livraison et démarrage de la fenêtre de réclamation.

**Acceptation :** DiddiShop ne crée jamais de second paiement pour une livraison
et aucun événement DiddiSend dupliqué ne double une transition.

**Tests :** création avec retry, événement avant réponse HTTP, progression
dupliquée, livraison échouée, retour confirmé, preuve manquante.

### P5 — Annulations, retours, réclamations et finance

**Objectif :** appliquer la matrice financière sans perdre la traçabilité.

À implémenter :

- expiration confirmation vendeur à 24 h ;
- annulation acheteur avant prise en charge ;
- annulation DiddiSend si elle est possible ;
- restitution de stock au maximum une fois ;
- demande de remboursement DiddiPay avec clé stable ;
- réclamation dans les 72 h après `DELIVERED` ;
- décision support : acheteur, vendeur ou remboursement partiel ;
- transition `RETURNED` → `CLOSED` après traitement ;
- distinction entre décision métier et confirmation financière DiddiPay ;
- audit de chaque décision et correction.

**Acceptation :** aucune release vendeur n’est déclenchée en V1 ; un timeout
DiddiPay reste `processing` et peut être repris avec la même clé ;
un remboursement confirmé est la seule preuve de l’état `REFUNDED`.

**Tests :** annulation concurrente avec prise en charge, remboursement reçu deux
fois, remboursement partiel, réclamation dans la fenêtre, retour imputé
acheteur/vendeur, panier multi-boutiques avec remboursement d’une seule commande.

### P6 — Rewards/campagnes, communication et support

**Objectif :** ajouter les capacités transverses sans créer de second moteur métier.

#### Rewards/campagnes

- projection locale des campagnes publiées utiles au checkout ;
- `quote`, `reserve`, `consume`, `release` via DiddiRewards ;
- conservation du `campaign_id`, `campaign_version`, `benefit_id` et des montants
  appliqués dans le snapshot de commande ;
- traitement des événements Rewards utiles à la cohérence de projection ;
- aucune écriture du ledger ou du budget dans DiddiShop.

#### Communication

- génération de tâches DiddiComms depuis l’outbox ;
- notifications commande créée, paiement confirmé, confirmation vendeur,
  expédition, livraison, réclamation et remboursement ;
- retries et receipts sans modifier l’état de commande ;
- déduplication par `event_id`.

#### Support

- contexte support agrégé : commande, lignes, paiement, livraison, preuves,
  timeline, remboursements et événements ;
- ouverture de cas DiddiSupport pour une réclamation ;
- décision support via un use case DiddiShop idempotent ;
- interdiction d’écriture directe dans les tables `orders` depuis Support.

**Acceptation :** une notification perdue est rejouable sans effet financier ;
un agent support peut comprendre une commande sans accès aux bases externes ;
Rewards ne devient pas propriétaire de la commande.

**Tests :** projection de campagne, réservation consommée/libérée, notification
dupliquée, contexte support complet, décision support répétée.

### P7 — DiddiBackoffice et préparation de production

**Objectif :** rendre le MVP opérable et auditable.

À implémenter :

- routes admin DiddiShop : recherche commande, réclamation, paiement, livraison ;
- commandes sensibles avec `Idempotency-Key`, acteur, justification et
  `correlation_id` ;
- adaptateur DiddiBackoffice ;
- audit local de la commande et audit opérateur côté backoffice ;
- dashboards : commandes par état, outbox bloquée, inbox doublons, remboursements
  en attente, réclamations ouvertes, erreurs externes ;
- runbook incident et procédure de réconciliation ;
- tests de sécurité S2S et permissions admin.

**Acceptation :** le backoffice ne lit aucune table DiddiShop directement ; une
commande sensible laisse une trace complète et peut être réconciliée.

## 5. Contrats d’événements à livrer

### Événements émis par DiddiShop

```text
checkout.created
order.created
order.confirmed
order.ready_for_pickup
order.cancelled
order.delivered
order.returned
claim.opened
claim.decided
```

### Événements reçus

```text
payment.succeeded
payment.failed
payment.refunded
delivery.created
delivery.picked_up
delivery.in_transit
delivery.delivered
delivery.failed
delivery.returned
rewards.campaign.published
rewards.entitlement.*
```

Chaque événement doit avoir une enveloppe versionnée, un `event_id`, un
`correlation_id`, un `causation_id` optionnel et un payload sans secret ni donnée
de carte.

## 6. Stratégie d’idempotence

| Surface | Clé | Règle |
| --- | --- | --- |
| Commande HTTP | `Idempotency-Key` client | même clé + même corps = même réponse ; corps différent = `409` |
| Événement entrant | `consumer + event_id` | doublon sans nouvel effet métier |
| Paiement | `shop:create-payment:{checkout_id}:1` | même montant et même checkout |
| Livraison | `shop:create-delivery:{order_id}:1` | même commande, jamais un nouveau paiement |
| Refund | `shop:refund:{order_id}:{operation}` | une opération financière = une clé |
| Notification | `shop:notify:{event_id}:1` | retry sans message métier dupliqué |

## 7. Jalons de livraison

| Jalon | Résultat attendu | Conditions de sortie |
| --- | --- | --- |
| M1 | Fondations et contrats | migrations, DI, outbox/inbox, tests verts |
| M2 | Catalogue achetable | boutique, produit, stock, médias, permissions |
| M3 | Checkout payable | panier multi-boutiques, PaymentIntent, webhooks |
| M4 | Expédition réelle | DiddiSend, événements de livraison, suivi |
| M5 | Finance MVP V1 | annulations, retours, claims, refunds sans release vendeur |
| M6 | Opérations transverses | Rewards, Comms, Support, Observe |
| M7 | Exploitation | Backoffice, audit, réconciliation, recette MVP |

## 8. Critères de recette MVP

Le MVP est accepté lorsque les scénarios suivants passent en intégration :

1. achat d’un produit d’une boutique jusqu’à livraison ;
2. achat multi-boutiques avec un seul paiement et plusieurs commandes ;
3. stock final soumis à deux checkouts concurrents ;
4. échec et retry de paiement ;
5. confirmation vendeur expirée ;
6. annulation avant prise en charge ;
7. livraison échouée puis retour ;
8. réclamation gagnée par l’acheteur ;
9. réclamation gagnée par le vendeur ;
10. remboursement partiel ;
11. absence de release vendeur automatique en V1 ;
12. événements entrants dupliqués ;
13. panne outbox puis reprise ;
14. tâche de notification dupliquée ;
15. action support et commande backoffice auditée.

## 9. Risques et décisions bloquantes

| Risque | Impact | Décision/mitigation |
| --- | --- | --- |
| Séquestration marketplace reportée en V2 | release vendeur non disponible en V1 | ne déclencher aucun hold/payout ; traiter le contrat en V2 |
| DiddiSend recrée un PaymentIntent | double débit | contrat `prepaid_by_origin` obligatoire |
| URL produit DiddiFiles non lisible | catalogue sans image fiable | endpoint signé/public à valider en P2 |
| événements externes sans signature ou version | fraude et transitions incohérentes | refuser l’événement avant validation |
| règles Rewards ambiguës | remise incorrecte | snapshot campagne/version obligatoire |
| backoffice écrit directement en base | perte d’audit et invariants contournés | API admin DiddiShop uniquement |

## 10. Prochaine tranche d’exécution

La prochaine tranche doit implémenter **P0 puis P1**, sans ajouter de nouvelle
fonctionnalité produit : base PostgreSQL, transactions, inbox/outbox,
idempotence, authentification et contrats mockés de DiddiPay/DiddiSend.

La tranche suivante pourra ensuite implémenter verticalement `shops → catalog →
cart → checkout/orders` avec ses tests d’intégration.
