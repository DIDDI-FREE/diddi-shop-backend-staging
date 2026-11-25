# Intégration DiddiRewards

DiddiRewards reste propriétaire des campagnes, benefits, budget et ledger.
DiddiShop conserve uniquement la décision et le snapshot nécessaires à la
commande.

## Parcours

```text
checkout -> quote
         -> reserve
paiement confirmé -> confirm/consume
annulation/retour -> release ou correct selon le contrat
```

Le checkout ne choisit pas automatiquement une campagne globale :
`rewards_campaign_id` doit être explicite lorsqu’un avantage est demandé.
Toutes les valeurs sont XOF et les opérations mutantes portent une clé stable.

Les routes dédiées DiddiShop `quote`, `reserve`, `confirm`, `release` et
`correct` sont derrière l’adaptateur. Le client Shop, les scopes, la campagne
publiée, le budget et la ventilation `professional_payout_minor` restent à
valider en staging.
