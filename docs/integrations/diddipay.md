# Intégration DiddiPay

En V1, DiddiShop utilise DiddiPay pour PaymentIntent, annulation, refund et
événements de paiement. Aucun hold marketplace ni release vendeur n’est actif.

## Mapping observé

`POST /payfund/v1/payment-intents` attend `business_reference`, `amount` et
`currency=XOF`. L’adaptateur DiddiShop transforme son modèle interne
`amount_minor` vers `amount` et normalise la réponse `id` en
`payment_intent_id`.

Pour le mobile money, il envoie `channel=mobile_money` et traduit `wave` vers
`network=wave`, `mtn_momo` vers `network=mtn` et `orange_money` vers
`network=orange`. Les champs `payment_method` et `return_url` ne font pas
partie du schéma DiddiPay staging et ne sont pas envoyés.

`recipient_phone` du checkout devient obligatoirement `customer_phone` dans
le JSON PaymentIntent, au format E.164 (`+` puis 8 à 15 chiffres). DiddiShop
conserve cette entrée indépendamment d'un éventuel champ nul dans la réponse
DiddiPay. Un retry réutilise ce téléphone ; pour les checkouts historiques,
il récupère à défaut le `recipient_phone` valide dans les commandes liées.
Si aucune valeur valide n'existe, DiddiShop retourne `422
PAYMENT_PHONE_REQUIRED` **avant** de changer la tentative ou d'appeler
DiddiPay. Aucun numéro n'est inventé et aucun ancien enregistrement n'est
supprimé.

Un refund attend `amount` et `reason`. La réponse `id` est normalisée en
`refund_id`. DiddiShop ne reçoit ni ne stocke de données carte.

## Idempotence et webhooks

- PaymentIntent : clé fournie à la création (`idempotency_key`), puis nouvelle
  `Idempotency-Key` pour chaque nouvelle tentative après un échec confirmé ;
- refund : `shop:refund:{order_id}:{operation}` ;
- DiddiPay signe l'enveloppe JSON compacte et triée avec HMAC-SHA256, sur les
  octets réellement transmis, puis l'envoie dans `X-DiddiPay-Signature` ;
- DiddiShop vérifie cette signature avec `DIDDI_SHOP_DIDDIPAY_WEBHOOK_SECRET`;
- ce secret entrant est différent du credential S2S DiddiShop → DiddiPay ;
- l'enveloppe reçue est `{id, type, occurred_at, data}` et `data.business_reference`
  est de la forme `diddishop:checkout:{checkout_id}` ;
- un événement déjà traité retourne un résultat `duplicate` sans nouvelle
  mutation.

Les statuts locaux `PENDING`, `REFUNDED` et `PARTIALLY_REFUNDED` ne remplacent
pas les statuts fournisseurs : le mapping doit être explicite.

### Distinguer un rejeu d'une nouvelle tentative

Les réponses de création et de retry portent `Idempotency-Replayed` :

- `true` : même clé déjà traitée, réponse mémorisée, aucun nouvel appel DiddiPay.
  Une ancienne erreur `customer_phone is required` peut donc être rejouée après
  un correctif, sans que le correctif ait été exécuté.
- `false` : opération nouvelle. Le retry incrémente `payment_attempt`.

Ne pas supprimer la déduplication pour forcer un paiement. Réutiliser la même
clé pour retransmettre une requête dont la réponse a été perdue ; utiliser une
clé **jamais utilisée** pour une nouvelle tentative après échec confirmé.
Les logs `checkout.payment.replayed`, `checkout.payment.intent_requested` et
`checkout.payment.intent_resolved` distinguent ces chemins. Ils n'exposent ni
numéro, ni clé d'idempotence, ni secret, ni corps de requête.

## V2

Le port de release vendeur reste désactivé en V1. Il ne sera activé qu’après
un contrat DiddiPay dédié pour hold, release, ledger, litiges, réconciliation
et événements.
