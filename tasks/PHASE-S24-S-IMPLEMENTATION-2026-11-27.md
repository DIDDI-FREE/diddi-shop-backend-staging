# S24-S — journal d’implémentation

## A/B/C — terminé

- États `refund_status` et codes `refund_method` typés dans la réponse claim.
- Normalisation en minuscules et fallback sur le moyen du paiement d’origine.
- Upload DiddiFiles documenté : reprendre exactement method, URL et headers ;
  confirmer puis joindre le fichier.
- Aucun TTL de fichier non joint inventé : seul le TTL de la signature est
  contractuellement établi.
- Vérification : `python -m pytest -q` → 239 passed.

## Déploiement

Déploiement manuel utilisateur en attente. Aucun remboursement ni upload réel
n’a été déclenché par l’agent.
