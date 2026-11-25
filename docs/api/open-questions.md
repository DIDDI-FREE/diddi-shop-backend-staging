# Questions ouvertes et contrats à valider

Cette page reprend le rôle de `open-questions.md` de DiddiGo. Une question
ouverte décrit une limite connue ; elle ne doit pas être transformée en
comportement implicite dans le code.

## DiddiSend

- Confirmer `prepaid_by_origin=true` pour les livraisons DiddiShop.
- Confirmer la ventilation financière XOF acceptée pour un marketplace, sans
  second débit côté DiddiSend.
- Confirmer les événements signés et leur catalogue final : création, prise en
  charge, transit, livraison, échec et retour.

## DiddiPay

- Le contrat PaymentIntent/refund V1 est aligné sur l’OpenAPI staging observée.
- Le hold marketplace et la release vendeur ne sont pas un contrat V1 ; ils
  sont reportés en V2.
- Confirmer les statuts et signatures des webhooks staging avec credentials.

## DiddiFiles

- Confirmer la visibilité et la durée des URLs pour le purpose
  `diddishop_product_image`.
- Confirmer la politique de téléchargement privé versus URL publique.

## DiddiFreeID

- Provisionner un client S2S distinct par service cible et injecter les secrets
  dans le secret manager.
- Confirmer les scopes finaux côté plateforme ; le code refuse les credentials
  manquants en environnement non développement.

## DiddiRewards

- Provisionner le client Shop, les scopes et une campagne publiée avec budget.
- Confirmer `professional_payout_minor` dans la ventilation V1.
- Confirmer la durée de réservation et les événements de correction.

## DiddiComms

- La route conversation ouvre ou retrouve une conversation métier ; elle ne
  déclenche pas une notification.
- Valider le resolver DiddiShop/type de tâche et l’autorisation S2S. Le contrat
  de notifications événementielles devra être séparé.

## DiddiSupport et DiddiObserve

- Confirmer l’enveloppe et les scopes des cas/contextes Support.
- Injecter le credential OTLP Basic dédié, vérifier les marqueurs API/worker,
  le scrape Prometheus et la corrélation trace réelle.

## Règle de validation

Une validation doit fournir : version du contrat, environnement, endpoint,
authentification attendue, exemple sans donnée sensible, comportement de
rejeu et résultat observé. Les sondes publiques `/health` et `/openapi.json`
ne constituent pas une recette authentifiée.
