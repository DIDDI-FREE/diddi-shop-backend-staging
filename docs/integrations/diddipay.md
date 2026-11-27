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
La **valeur** `return_url` Shop est en revanche transmise sous le nom
contractuel `callback_url` (correction S24-O). Une cible serveur `return_target`
peut la remplacer ; les deux ne sont jamais envoyées ensemble.

`recipient_phone` du checkout devient obligatoirement `customer_phone` dans
le JSON PaymentIntent, au format E.164 (`+` puis 8 à 15 chiffres). DiddiShop
conserve cette entrée indépendamment d'un éventuel champ nul dans la réponse
DiddiPay. Un retry réutilise ce téléphone ; pour les checkouts historiques,
il récupère à défaut le `recipient_phone` valide dans les commandes liées.
Si aucune valeur valide n'existe, DiddiShop retourne `422
PAYMENT_PHONE_REQUIRED` **avant** de changer la tentative ou d'appeler
DiddiPay. Aucun numéro n'est inventé et aucun ancien enregistrement n'est
supprimé.

## Retour navigateur et Payment Page

Par défaut, le retour est
`https://diddishop-backend.diddifree.com/payments/return` : une page HTML Shop
publique, sans données personnelles, sans confirmation de paiement. Ce
principe reprend DiddiSend/DiddiGo ; l'application peut conserver l'identifiant
checkout et relire `GET /v1/checkouts/{id}` au retour. Aucun paramètre navigateur
(`status`, `reference`, etc.) ne modifie le paiement.

Configuration non sensible :

```ini
DIDDI_SHOP_DIDDIPAY_RETURN_URL=https://diddishop-backend.diddifree.com/payments/return
DIDDI_SHOP_DIDDIPAY_RETURN_TARGET=
```

Un target configuré prévaut sur l'URL par défaut. Il doit déjà être enregistré
**par DiddiPay** sous la clé `<client S2S Shop vers Pay>:<target>` dans
`PAYMENT_CHECKOUT_RETURN_TARGETS`. Aucun target Shop n'est supposé provisionné.
Le mode `callback_url` est accepté seulement si DiddiPay autorise son fallback
et cette origine/ce chemin. DiddiShop ne change pas ces règles chez DiddiPay.
Ce réglage est **distinct** de `PAYMENT_CALLBACK_TARGETS`, qui concerne les
webhooks HMAC et non le retour du navigateur.

Priorité à la création : option explicite du corps, sinon configuration. Au
retry : option explicite, snapshot paiement, ancienne commande, configuration.
L'URL ou la cible résolue est conservée même si Pay ne l'écho pas. Un corps
facultatif de retry permet de corriger la destination, avec une clé nouvelle.
URL : HTTPS, domaine `diddifree.com` ou sous-domaine, port 443/default,
1–2048 caractères, sans credentials, fragment ou traversée de chemin.
Target : 1–64 caractères, exclusif de l'URL. HTTP et localhost sont refusés.
Sans destination : `422 PAYMENT_RETURN_REQUIRED` avant effets métier ;
configuration invalide : `422 PAYMENT_RETURN_INVALID`.

Quand Pay répond `requires_action` avec `next_action.type=redirect`, Shop reste
`payment_pending`, relaie `next_action` et expose son `url` comme `payment_url`.
Le frontend ouvre cette URL (elle peut être à usage unique, ne pas la journaliser).
`next_action` contient `type`, `url?`, `instructions?`, `expires_at?` ; les types
sont `redirect`, `mobile_money_prompt`, `display_instructions`,
`await_confirmation`, `none`. L'expiration est également exposée dans
`payment.expires_at` si fournie, jamais inventée.

Les refus HTTP 422 explicites `PAYMENT_RETURN_TARGET_CONFLICT`,
`PAYMENT_RETURN_TARGET_FORBIDDEN`, `PAYMENT_CALLBACK_URL_DISABLED` et
`PAYMENT_CALLBACK_URL_FORBIDDEN` sont persistés comme `payment_failed`, avec
le code dans `payment_failure_code`, `provider_status=rejected_by_diddipay`
et aucun identifiant d'intention inventé. La réponse Shop reste HTTP 200 et
contient ce résultat d'échec, permettant de corriger puis retenter. Un timeout,
5xx ou autre rejet inconnu n'est pas transformé en échec certain autorisant
aveuglément un nouveau prélèvement.

Contrat vérifié : [OpenAPI DiddiPay staging](https://pay-api-staging.diddifree.com/payfund/v1/openapi.json),
resolver et adaptateur Payment Page lus le 27 novembre 2026. Les tests utilisent
un fournisseur simulé ; ils ne prouvent ni la configuration Pay en cours ni
la réussite d'un prélèvement réel.

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

Après un `payment.succeeded` traité, le checkout est `payment_succeeded`,
la commande est `TO_CONFIRM` et son statut paiement local historique est
`HELD`. Ce dernier nom ne déclenche aucune séquestration V1. La confirmation
paiement, l'historique et les métadonnées Rewards sont conservés après lecture
et sauvegarde SQL.

Si la sauvegarde Shop échoue en 500, le callback n'est pas acquitté dans
l'inbox. Faire reprendre la notification originale par DiddiPay, **pas le
paiement**. Procédure : [runbook de reprise](../operations/runbook.md#paiement-reussi-chez-diddipay-mais-webhook-shop-en-500).

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
