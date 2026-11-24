# DiddiShop — Spécification backend du MVP cadré

**Version :** 1.1 — 24 novembre 2026  
**Statut :** proposition prête pour découpage en tickets

## 1. Décision de périmètre

Le MVP couvre le parcours complet d'une marketplace de produits physiques, avec paiement dans l'application et livraison par DiddiSend.

### 1.1 Inclus dans le MVP

- création d'une boutique par vendeur ;
- catalogue de produits physiques : titre, description, prix, photos, catégorie et stock ;
- navigation, recherche simple et fiche produit ;
- panier multi-boutiques ;
- validation d'un panier avec une adresse de livraison ;
- un paiement DiddiPay par validation de panier ;
- une commande DiddiShop par boutique ;
- confirmation vendeur sous 24 heures ;
- création et suivi d'une livraison DiddiSend ;
- annulation avant la prise en charge par le coursier ;
- gestion des livraisons échouées et des retours ;
- réclamation acheteur sous 72 heures après livraison ;
- libération du vendeur après 72 heures sans réclamation ;
- remboursement, historique des statuts, notifications et accès admin en lecture ;
- signalement simple d'une boutique ou d'un article ;
- audit des décisions de support et des changements de configuration.

### 1.2 Explicitement hors MVP

Ces éléments sont reportés après validation du parcours physique principal :

- produits digitaux, téléchargement, cours vidéo et bibliothèque ;
- paiement à la livraison ;
- variantes de produit (taille, couleur) ;
- employés et rôles avancés dans une boutique ;
- promotions, coupons, soldes et prix personnalisés ;
- avis et réponses vendeur ;
- scoring acheteur/vendeur ;
- livraison partielle d'une même commande ;
- recherche avancée, recommandations et moteur de classement ;
- retrait vendeur depuis DiddiShop : le solde et le retrait restent dans DiddiPay.

### 1.3 Simplifications assumées

- Une validation de panier crée un paiement DiddiPay et une ou plusieurs commandes DiddiShop.
- DiddiPay est responsable de la répartition comptable du paiement entre les commandes.
- Une commande appartient à une seule boutique et contient uniquement des produits physiques.
- Le stock n'est pas réservé dans le panier. Il est décrémenté atomiquement à la validation.
- Les frais de livraison sont obtenus avant le paiement et figés sur la validation du panier et sur chaque commande.
- Le paiement vendeur n'est jamais calculé à partir des données courantes du catalogue : les montants sont figés dans la commande.
- Une commande ne peut pas être supprimée physiquement. Les données sont conservées pour l'audit et les obligations de preuve.

## 2. Modèle financier de référence

Pour chaque commande :

```text
montant_articles = somme(prix_unitaire_figé × quantité)
frais_livraison = devis DiddiSend figé pour cette commande
total_acheteur = montant_articles + frais_livraison
commission = arrondi(montant_articles × 10 %)
net_vendeur = montant_articles - commission - retenues éventuelles décidées par DiddiPay
```

La commission ne s'applique jamais aux frais de livraison. Les arrondis sont effectués en francs CFA entiers selon une règle unique définie par DiddiPay et reprise dans le contrat d'intégration.

Le MVP utilise les paramètres suivants :

| Paramètre | Valeur initiale | Source |
| --- | ---: | --- |
| Commission sur les articles | 10 % | configuration versionnée |
| Délai de confirmation vendeur | 24 h | configuration opérationnelle |
| Délai avant libération | 72 h | configuration opérationnelle |
| Fenêtre de réclamation | 72 h après livraison | configuration opérationnelle |
| Paiement à la livraison | Désactivé | décision de périmètre |

Les paramètres qui influencent une commande sont copiés dans son snapshot financier au moment de la validation.

## 3. Machine à états des commandes

### 3.1 Deux axes indépendants

Le statut logistique et le statut financier sont séparés. Un remboursement ne doit pas obliger à réécrire l'historique logistique, et une livraison ne doit pas être considérée comme un paiement libéré.

#### Statut logistique (`fulfillment_status`)

| Statut | Signification | Terminal |
| --- | --- | --- |
| `PAYMENT_PENDING` | Commande créée, paiement DiddiPay non confirmé | Non |
| `TO_CONFIRM` | Paiement confirmé, attente de confirmation vendeur | Non |
| `TO_PREPARE` | Vendeur a confirmé la commande | Non |
| `READY_FOR_PICKUP` | Colis prêt, demande DiddiSend créée | Non |
| `PICKED_UP` | Colis remis au coursier | Non |
| `IN_TRANSIT` | Colis en route | Non |
| `DELIVERED` | Livraison confirmée par code ou photo | Non |
| `RETURNED` | Colis retourné à la boutique | Oui, sauf traitement admin exceptionnel |
| `CANCELLED` | Commande annulée avant livraison | Oui |
| `FAILED` | Livraison définitivement échouée sans retour exploitable | Oui |
| `DISPUTED` | Réclamation ouverte, livraison déjà effectuée | Non |
| `CLOSED` | Traitement final terminé après livraison ou retour | Oui |

#### Statut financier (`payment_status`)

| Statut | Signification | Terminal |
| --- | --- | --- |
| `PENDING` | Paiement non confirmé | Non |
| `HELD` | Paiement confirmé et conservé dans le séquestre | Non |
| `REFUND_PENDING` | Remboursement demandé à DiddiPay | Non |
| `REFUNDED` | Remboursement confirmé | Oui |
| `RELEASE_BLOCKED` | Libération bloquée par une réclamation ou un incident | Non |
| `RELEASE_PENDING` | Libération demandée à DiddiPay | Non |
| `RELEASED` | Net vendeur libéré | Oui |
| `PARTIALLY_REFUNDED` | Remboursement partiel confirmé | Non |

### 3.2 Transitions autorisées

| Depuis | Action ou événement | Vers | Autorité | Conditions |
| --- | --- | --- | --- | --- |
| — | Validation du panier | `PAYMENT_PENDING` | Acheteur | Stock décrémenté atomiquement, paiement créé |
| `PAYMENT_PENDING` | `payment.succeeded` | `TO_CONFIRM` | DiddiPay | Événement authentique et inédit |
| `PAYMENT_PENDING` | `payment.failed` ou expiration | `CANCELLED` | Système | Stock rendu une seule fois |
| `TO_CONFIRM` | Confirmation vendeur | `TO_PREPARE` | Vendeur | Dans les 24 h |
| `TO_CONFIRM` | Expiration 24 h | `CANCELLED` | Système | Remboursement demandé |
| `TO_CONFIRM` | Annulation acheteur | `CANCELLED` | Acheteur | Tant que le colis n'est pas pris en charge |
| `TO_PREPARE` | Colis prêt | `READY_FOR_PICKUP` | Vendeur | Gabarit et adresse de retrait valides |
| `TO_PREPARE` | Annulation acheteur | `CANCELLED` | Acheteur | Avant prise en charge |
| `READY_FOR_PICKUP` | `delivery.created` | `READY_FOR_PICKUP` | DiddiSend | Référence livraison enregistrée |
| `READY_FOR_PICKUP` | `delivery.picked_up` | `PICKED_UP` | DiddiSend | Annulation acheteur désormais refusée |
| `PICKED_UP` | `delivery.in_transit` | `IN_TRANSIT` | DiddiSend | — |
| `IN_TRANSIT` ou `PICKED_UP` | `delivery.delivered` | `DELIVERED` | DiddiSend | Code ou photo obligatoire |
| `PICKED_UP` ou `IN_TRANSIT` | `delivery.failed` | `RETURNED` ou `FAILED` | DiddiSend | Selon retour confirmé |
| `DELIVERED` | Ouverture d'une réclamation | `DISPUTED` | Acheteur | Dans les 72 h |
| `DELIVERED` | Fin de délai sans réclamation | `CLOSED` | Système | Libération autorisée |
| `DISPUTED` | Décision support pour l'acheteur | `CLOSED` | Support | Remboursement confirmé ou en cours |
| `DISPUTED` | Décision support pour le vendeur | `CLOSED` | Support | Libération autorisée |
| `RETURNED` | Retour confirmé et traitement financier terminé | `CLOSED` | Système/support | Remboursement ou libération traité |

Toute autre transition est refusée. Chaque transition valide crée une entrée immuable dans `order_status_history` avec l'acteur, la source, le motif, la date et l'identifiant de corrélation.

### 3.3 Règles d'invariance

- Une commande ne peut être livrée que si son paiement est `HELD`, `RELEASE_BLOCKED` ou déjà traité par DiddiPay.
- Une commande annulée ne peut jamais repasser dans un état actif.
- Le stock est rendu au maximum une fois par commande et par ligne.
- Une libération vendeur ne peut être demandée qu'une seule fois.
- Une réclamation ouverte bloque la libération jusqu'à sa décision.
- Les événements DiddiPay et DiddiSend ne modifient jamais directement le stock.
- Une commande multi-boutiques ne partage pas son statut logistique avec les autres commandes du panier.

## 4. Contrats d'événements

### 4.1 Enveloppe commune

Tous les événements internes et inter-services utilisent une enveloppe versionnée :

```json
{
  "event_id": "evt_01J...",
  "event_type": "order.confirmed",
  "event_version": 1,
  "occurred_at": "2026-11-24T12:00:00Z",
  "producer": "diddi-shop",
  "aggregate_type": "order",
  "aggregate_id": "ord_01J...",
  "correlation_id": "chk_01J...",
  "causation_id": "evt_01J...",
  "payload": {}
}
```

Obligations :

- `event_id` est unique et immuable ;
- `event_type` est stable et suit la convention `objet.action` ;
- une évolution incompatible crée une nouvelle `event_version` ;
- `correlation_id` relie les événements d'un même checkout ;
- `causation_id` relie un événement à l'action qui l'a déclenché ;
- aucun secret, token, adresse complète ou donnée de carte bancaire n'est publié ;
- les montants sont toujours des entiers en XOF dans le contrat métier ; aucune conversion de devise n'est autorisée.

### 4.2 Événements publiés par DiddiShop

| Type | Déclencheur | Payload minimale | Consommateurs |
| --- | --- | --- | --- |
| `order.created` | Commande créée avec paiement en attente | `order_id`, `checkout_id`, `shop_id`, `amount_items`, `delivery_fee`, `total`, `currency` | Notifications, admin |
| `order.confirmed` | Vendeur confirme | `order_id`, `shop_id`, `confirmed_at` | Notifications |
| `order.cancelled` | Annulation validée | `order_id`, `reason`, `cancelled_by`, `refund_amount` | DiddiPay, notifications, score futur |
| `order.ready_for_pickup` | Colis prêt | `order_id`, `shop_id`, `pickup_address_ref`, `package_template` | DiddiSend |
| `order.delivered` | Livraison confirmée | `order_id`, `delivery_id`, `proof_type`, `delivered_at` | Notifications, timer de réclamation |
| `order.returned` | Retour à la boutique confirmé | `order_id`, `delivery_id`, `reason`, `attribution` | DiddiPay, notifications |
| `claim.opened` | Réclamation créée | `claim_id`, `order_id`, `reason`, `opened_at` | Support, notifications |
| `claim.decided` | Décision support | `claim_id`, `order_id`, `decision`, `reason`, `amount_to_refund` | DiddiPay, notifications |
| `seller.release.requested` | Libération autorisée | `order_id`, `amount_items`, `commission`, `net_seller`, `eligible_at` | DiddiPay |

### 4.3 Événements reçus par DiddiShop

#### DiddiPay

| Type | Payload minimale | Effet |
| --- | --- | --- |
| `payment.succeeded` | `payment_id`, `checkout_id`, `amount`, `currency`, `paid_at` | Chaque commande liée passe à `TO_CONFIRM`, paiement `HELD` |
| `payment.failed` | `payment_id`, `checkout_id`, `reason`, `failed_at` | Commandes non confirmées annulées, stock rendu |
| `payment.refunded` | `payment_id`, `order_id`, `amount`, `refund_id`, `refunded_at` | Statut financier `REFUNDED` ou `PARTIALLY_REFUNDED` |
| `seller.release.completed` | `order_id`, `release_id`, `amount`, `released_at` | Statut financier `RELEASED` |

#### DiddiSend

| Type | Payload minimale | Effet |
| --- | --- | --- |
| `delivery.created` | `delivery_id`, `order_id`, `quoted_fee` | Référence livraison enregistrée |
| `delivery.picked_up` | `delivery_id`, `order_id`, `occurred_at` | Passage à `PICKED_UP` |
| `delivery.in_transit` | `delivery_id`, `order_id`, `occurred_at` | Passage à `IN_TRANSIT` |
| `delivery.delivered` | `delivery_id`, `order_id`, `proof_type`, `proof_ref`, `occurred_at` | Passage à `DELIVERED`, démarrage des délais |
| `delivery.failed` | `delivery_id`, `order_id`, `reason`, `attribution`, `occurred_at` | Traitement d'échec et retour |
| `delivery.returned` | `delivery_id`, `order_id`, `occurred_at` | Passage à `RETURNED` |

### 4.4 Outbox et livraison

Lorsqu'une commande change d'état, la modification de commande, l'historique et l'enregistrement outbox sont écrits dans la même transaction de base de données. Un worker publie ensuite l'outbox.

Champs minimum de l'outbox : `id`, `event_id`, `event_type`, `aggregate_id`, `payload`, `attempts`, `available_at`, `published_at`, `last_error`.

Une publication échouée est réessayée avec backoff. Après le seuil configuré, elle est placée en file d'incident et alerte le support technique ; elle n'est jamais supprimée silencieusement.

## 5. Idempotence et déduplication

### 5.1 Événements entrants

Chaque consommateur possède une table `processed_events` contenant au minimum : `consumer`, `event_id`, `event_type`, `processed_at`, `result_hash`.

Le traitement suit cette séquence transactionnelle :

1. commencer une transaction ;
2. insérer `(consumer, event_id)` avec contrainte unique ;
3. si la clé existe déjà, retourner un succès sans rejouer l'effet métier ;
4. vérifier l'identité de l'agrégat et la version attendue ;
5. appliquer la transition autorisée ;
6. écrire l'historique et les éventuels événements outbox ;
7. valider la transaction.

Un même `event_id` reçu avec un payload différent est une erreur de contrat et déclenche une alerte.

### 5.2 Commandes externes sortantes

Les appels vers DiddiPay et DiddiSend utilisent une clé d'idempotence stable :

```text
shop:{action}:{aggregate_id}:{operation_number}
```

Exemples :

- `shop:create-payment:chk_123:1` ;
- `shop:create-delivery:ord_123:1` ;
- `shop:refund:ord_123:1` ;
- `shop:release:ord_123:1`.

Une nouvelle tentative reprend la même clé. Une nouvelle opération financière légitime utilise un nouveau numéro, jamais une clé réutilisée avec un autre montant.

### 5.3 Idempotence des actions utilisateur

Les commandes HTTP d'écriture acceptent une clé `Idempotency-Key`. Elle est liée à l'utilisateur, à la route et au corps normalisé de la requête, conservée pendant au moins 24 heures.

Une répétition avec la même clé et le même corps retourne la même réponse. Une répétition avec la même clé et un corps différent est refusée avec `409 Conflict`.

## 6. Matrice financière

### 6.1 Règles générales

- La somme débitée au client est celle du checkout, jamais un recalcul après commande.
- Le paiement est conservé par DiddiPay jusqu'à libération, remboursement ou décision de réclamation.
- Les frais de livraison ne donnent pas lieu à commission vendeur.
- Le délai de libération commence à la confirmation de livraison par code ou photo.
- Une réclamation ouverte bloque la libération de la commande concernée uniquement.
- Les montants de remboursement sont demandés à DiddiPay par `order_id` et `payment_id`.
- Un remboursement confirmé est la seule preuve permettant de marquer l'argent comme remboursé dans DiddiShop.

### 6.2 Scénarios

| Scénario | Déclencheur | Stock | Remboursement acheteur | Livraison | Commission | Vendeur | Statut final |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Paiement échoué | DiddiPay refuse ou expire le paiement | Rendu une fois | Articles + livraison, si débit préautorisé | Aucune livraison créée | 0 | 0 | `CANCELLED` / `REFUNDED` si nécessaire |
| Vendeur ne confirme pas | Délai de 24 h dépassé | Rendu une fois | Articles + livraison | Aucune livraison ou livraison annulée | 0 | 0 | `CANCELLED` / `REFUNDED` |
| Acheteur annule avant prise en charge | Annulation valide | Rendu une fois | Articles + livraison | Devis annulé | 0 | 0 | `CANCELLED` / `REFUNDED` |
| Vendeur met le colis prêt puis acheteur annule avant prise en charge | Annulation valide | Rendu une fois | Articles + livraison, sous réserve du coût déjà irréversible signalé par DiddiSend | Livraison annulée | 0 | 0 | `CANCELLED` / `REFUNDED` |
| Livraison réussie, aucune réclamation | Délai de 72 h écoulé | Non | 0 | Frais conservés selon le contrat DiddiSend | 10 % des articles | Net vendeur libéré | `CLOSED` / `RELEASED` |
| Acheteur absent ou changement d'avis | Livraison échouée, retour confirmé, imputé acheteur | Stock retourné à la boutique | Montant des articles ; frais de livraison aller non remboursés | Retour pris en charge par la plateforme dans le MVP | 0 si remboursement des articles | 0 avant décision ; stock récupéré | `CLOSED` après remboursement |
| Article non conforme ou abîmé | Livraison échouée/réclamation, imputé vendeur | Stock retourné ou détruit selon support | Articles + livraison | Retour pris en charge par la plateforme dans le MVP | 0 | 0 | `CLOSED` / `REFUNDED` |
| Réclamation gagnée par l'acheteur | Support décide pour l'acheteur | Selon décision | Articles + livraison, ou montant décidé | Retour selon décision | Commission annulée | 0 | `CLOSED` / `REFUNDED` |
| Réclamation gagnée par le vendeur | Support décide pour le vendeur | Non | 0 | Frais conservés | 10 % des articles | Net vendeur libéré | `CLOSED` / `RELEASED` |
| Réclamation rejetée après expiration ou preuve insuffisante | Support clôture sans remboursement | Non | 0 | Frais conservés | 10 % des articles | Net vendeur libéré | `CLOSED` / `RELEASED` |
| Remboursement partiel décidé par support | Décision motivée | Selon décision | Montant explicite dans la décision | Frais remboursés ou non selon décision | Recalculée sur la part non remboursée | Solde libéré après remboursement | `CLOSED` / `PARTIALLY_REFUNDED` ou `RELEASED` |

### 6.3 Décisions à confirmer avant mise en production

Les choix suivants sont fixés comme défaut MVP dans cette version, mais doivent être validés par DiddiPay, DiddiSend et le produit :

1. La plateforme absorbe le coût du retour dans le MVP ; une retenue vendeur pourra être ajoutée plus tard sans modifier l'historique de commande.
2. En cas d'absence ou de changement d'avis de l'acheteur, les frais aller ne sont pas remboursés.
3. Une commande retournée pour faute vendeur donne droit au remboursement des articles et de la livraison.
4. Une décision de réclamation est définitive dans le MVP ; toute correction passe par une opération support auditée, jamais par une modification de l'historique.
5. Un panier multi-boutiques peut produire plusieurs remboursements séparés, un par commande, même si le client n'a effectué qu'un seul paiement.

## 7. Critères de validation du MVP

Le MVP est considéré techniquement prêt lorsque les scénarios suivants sont automatisés en test d'intégration :

- double validation simultanée du dernier stock ;
- paiement reçu deux fois ;
- webhook paiement reçu avant la réponse de création du paiement ;
- webhook livraison reçu deux fois ;
- expiration vendeur et confirmation concurrentes ;
- annulation concurrente avec prise en charge du colis ;
- panier de trois boutiques avec remboursement d'une seule commande ;
- réclamation ouverte juste avant la demande de libération ;
- retry après timeout de l'appel remboursement ou libération ;
- panne du worker outbox puis reprise sans événement perdu ni doublé.
