# Intégration DiddiSend

DiddiSend est l’unique propriétaire de l’expédition DiddiShop. DiddiShop ne
connaît ni les coursiers, ni la flotte, ni le géocodage opérationnel.

## Appels

| Opération | Contrat local | Clé |
| --- | --- | --- |
| Quote | `DeliveryQuote` | clé de quote du checkout |
| Création | `DeliveryRequest` | `shop:create-delivery:{order_id}:1` |
| Lecture | projection par `delivery_id` | — |
| Annulation | opération autorisée par DiddiSend | `shop:cancel-delivery:{order_id}:{operation}` |

## Authentification S2S

DiddiShop demande à DiddiFreeID un token `client_credentials` dédié à
`diddisend`, avec les scopes `diddisend:deliveries:quote`,
`diddisend:deliveries:create`, `diddisend:deliveries:read` et
`diddisend:deliveries:cancel`. Le scope de création est `create`, pas
`write` : il doit être déclaré exactement ainsi par DiddiFreeID et accepté par
la version DiddiSend déployée.

Le client staging à utiliser est `diddishop-staging-diddisend`, avec l’audience
`diddisend` et l’origine `diddishop`. DiddiShop transmet sur chaque appel :

```http
Authorization: Bearer <JWT client_credentials>
X-Client-ID: diddishop-staging-diddisend
X-Origin-Service: diddishop
X-User-ID: <UUID du sender technique>
```

Les variables explicites `DIDDISEND_CLIENT_ID`, `DIDDISEND_CLIENT_SECRET`,
`DIDDISEND_AUDIENCE`, `DIDDISEND_ORIGIN_SERVICE` et
`DIDDISEND_SERVICE_USER_ID` sont prioritaires sur l’entrée `diddisend` de la
map générique. Le secret client reste injecté par Portainer et n’est jamais
commité. `DIDDISEND_SERVICE_USER_ID` doit être un UUID technique autorisé par
DiddiSend ; il est aussi utilisé comme `sender_user_id` dans la création de
livraison.

La création exige aussi les coordonnées du sender technique :

```ini
DIDDISEND_SENDER_PHONE=<telephone-du-sender-technique-autorise>
DIDDISEND_SENDER_EMAIL=<email-du-sender-technique-autorise>
```

Ces valeurs doivent correspondre au sender autorisé côté DiddiSend. En staging,
l’application refuse de démarrer si elles sont absentes, afin d’éviter un HTTP
422 tardif après le passage à `READY_FOR_PICKUP`.

## Déclenchement depuis l’application vendeur

Le vendeur ne contacte jamais DiddiSend directement. Lorsque la préparation est
terminée, l’application appelle :

```http
POST /v1/orders/{order_id}/ready
Authorization: Bearer <acheteur-ou-vendeur-token>
```

DiddiShop vérifie que la commande est `TO_PREPARE`, la passe à
`READY_FOR_PICKUP`, puis appelle immédiatement DiddiSend avec la clé
`shop:create-delivery:{order_id}:1`. La réponse de DiddiSend est projetée dans
DiddiShop sous `delivery_id`.

Si la requête frontend expire après le changement d’état, le même appel peut
être rejoué. Une projection existante est renvoyée et aucune deuxième livraison
n’est créée. La route `POST /v1/deliveries/orders/{order_id}` est réservée à la
reprise contrôlée par l’exploitation.

Le payload porte `origin_module=diddishop`, `order_reference`,
`sender_phone`, `sender_email`, pickup/dropoff, colis,
`payment_method=diddipay`, `quoted_price`,
`prepaid_by_origin=true` et éventuellement `financial_breakdown`. Aucun
paiement n’est recréé dans DiddiSend.

## Événements

Les événements utiles sont `delivery.created`, `delivery.picked_up`,
`delivery.in_transit`, `delivery.delivered`, `delivery.failed` et
`delivery.returned`. Ils entrent par le webhook signé, passent par l’inbox et
mettent à jour la projection locale.

DiddiSend signe ses callbacks avec HMAC-SHA256 dans
`X-DiddiSend-Signature` sous la forme `sha256=<digest>`. DiddiShop vérifie la
signature avec `DIDDI_SHOP_DIDDISEND_WEBHOOK_SECRET`. L’enveloppe contient
`delivery_id` et `order_reference=shop-order:{order_id}` ; elle est adaptée
vers l’événement interne avant projection. Le secret DiddiSend entrant est
distinct des credentials S2S sortants.

DiddiSend doit être configuré avec l’URL suivante et le même secret HMAC que
celui injecté dans DiddiShop :

```ini
DIDDISEND_DIDDISHOP_WEBHOOK_URL=https://diddishop-backend.diddifree.com/internal/v1/webhooks/diddisend
DIDDISEND_DIDDISHOP_WEBHOOK_SECRET=<secret-partage-diddisend-shop>
```

Ce secret est différent du secret de callback DiddiPay et du secret client
`DIDDISEND_CLIENT_SECRET`.

## Point à valider

La recette staging doit confirmer que le client reçoit bien les quatre scopes,
que le sender technique est autorisé et que les appels quote/create/read/cancel
retournent les résultats attendus. Le mode prépayé est fixé à
`prepaid_by_origin=true` et la devise métier est exclusivement XOF.
