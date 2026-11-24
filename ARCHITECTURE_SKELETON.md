# DiddiShop — squelette d’architecture

## 1. Découpage de responsabilité

| Module | Possède | Ne possède pas | Connexion sortante |
| --- | --- | --- | --- |
| `shops` | boutiques, profil vendeur, statut boutique | paiement, livraison | DiddiFiles pour les images |
| `catalog` | produits, prix figés à la commande, stock | panier, paiement | DiddiFiles pour les photos |
| `cart` | panier courant et regroupement par boutique | commande persistée, stock définitif | ports catalogue/pricing |
| `checkout` | validation atomique, snapshot financier, création du paiement | PaymentIntent interne | DiddiPay, Rewards |
| `orders` | commande, lignes, machine d’états, historique, outbox | exécution du paiement/livraison | DiddiPay, DiddiSend |
| `claims` | réclamation, décision support, blocage de libération | transfert financier | DiddiSupport, DiddiPay |
| `rewards` | lecture/consommation des avantages appliqués à un checkout | définition globale des campagnes | DiddiRewards |
| `campaigns` | projection locale des campagnes publiées utiles au checkout | ledger et budget de campagne | DiddiRewards |
| `comms` | demande de notification métier et préférences minimales | livraison des SMS/messages | DiddiComms |
| `support` | contexte support exposé, références et timeline | décision financière autonome | DiddiSupport |
| `observability` | corrélation, métriques, logs structurés, traces | données métier de commande | DiddiObserve |
| `admin` | commandes administratives DiddiShop et audit local | données sources des autres modules | DiddiBackoffice/adaptateur |
| `audit` | journal immuable des décisions sensibles | état transactionnel métier | DiddiObserve / backoffice |

## 2. Connexions externes

### DiddiSend comme seule frontière d’expédition

DiddiShop ne connaît ni les coursiers ni les capacités opérationnelles d’un
autre service. Le seul contrat logistique du marketplace est DiddiSend :

```text
DiddiShop -> DiddiSend (quote/create/read/cancel delivery)
```

DiddiShop ne dépend d’aucun endpoint interne de gestion de coursiers. Les
détails éventuels de flotte restent entièrement dans DiddiSend.

### Contrats minimums

| Service | Appel depuis DiddiShop | Événements consommés |
| --- | --- | --- |
| DiddiPay | créer PaymentIntent, demander refund, demander release | `payment.succeeded`, `payment.failed`, `payment.refunded`, `seller.release.completed` |
| DiddiSend | quote, créer, lire et annuler une livraison | `delivery.created`, `delivery.picked_up`, `delivery.in_transit`, `delivery.delivered`, `delivery.failed`, `delivery.returned` |
| DiddiFiles | créer/confirm upload et lire metadata/URL | aucun événement obligatoire au MVP |
| DiddiRewards | quote/reserve/consume/release d’un bénéfice, lecture campagne | `rewards.*` utiles au checkout |
| DiddiComms | créer une tâche de notification | receipts de livraison optionnels |
| DiddiSupport | créer/enrichir un cas et transmettre le contexte | `support.case.*` optionnels |
| DiddiObserve | exporter logs, métriques et traces | aucun événement métier |
| DiddiFreeID | identité humaine et tokens S2S | aucun événement métier |
| DiddiBackoffice | accès admin DiddiShop via routes dédiées | aucun accès direct à la base DiddiShop |

## 3. Modules inclus dans le squelette

```text
app_base/
├── core/                    # composition, auth, DB, outbox, observabilité
├── shared_kernel/contracts/ # envelope d’événement et DTO externes stables
├── modules/
│   ├── shops/
│   ├── catalog/
│   ├── cart/
│   ├── checkout/
│   ├── orders/
│   ├── claims/
│   ├── rewards/
│   ├── campaigns/
│   ├── comms/
│   ├── support/
│   ├── observability/
│   ├── audit/
│   └── admin/
├── integrations/            # adaptateurs HTTP S2S isolés
└── workers/                 # outbox et consommateurs entrants
```

Chaque module métier a la forme :

```text
domain/{entities,interfaces}.py
application/{commands,services}.py
infra/{models,repositories}.py
presentation/{router,schemas}.py
```

## 4. Règles de frontière

1. Les transitions de commande sont exécutées seulement par `orders`.
2. Les événements entrants passent par une inbox idempotente avant toute mutation.
3. L’outbox est écrit dans la même transaction que l’état métier.
4. Les appels externes portent une `Idempotency-Key` stable et un `X-Request-ID`.
5. DiddiPay ne reçoit jamais de données de carte depuis DiddiShop.
6. DiddiShop ne déduit jamais le net vendeur à partir du catalogue courant.
7. Le backoffice commande via API et possède son propre audit opérateur.
8. Les erreurs d’un service externe sont normalisées par l’adaptateur, pas par le domaine.

## 5. Points à contractualiser avant implémentation réelle

- DiddiPay : contrat marketplace explicite pour hold, refund partiel et release vendeur.
- DiddiSend : mode `prepaid_by_origin` pour éviter de recréer un PaymentIntent lorsque
  DiddiShop possède déjà le checkout.
- DiddiFiles : rendre `diddishop_product_image` lisible via URL signée ou endpoint public.
- DiddiObserve : confirmer l’endpoint/protocole d’export, sans coupler DiddiShop à un SDK.
- DiddiRewards : confirmer les scopes DiddiShop et les événements de campagne applicables.
