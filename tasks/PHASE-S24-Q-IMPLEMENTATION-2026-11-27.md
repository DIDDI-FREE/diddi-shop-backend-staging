# S24-Q — journal d’implémentation

## A/B — terminé

- Ajout de `DIDDISEND_SENDER_PHONE` et `DIDDISEND_SENDER_EMAIL` dans les
  settings et les Compose/templates.
- Injection dans `delivery_request`, puis sérialisation par l’adaptateur
  DiddiSend sous `sender_phone` et `sender_email`.
- Validation non-development : configuration incomplète refusée explicitement.
- L’email est facultatif : à défaut, génération stable à partir du téléphone
  (`digits@diddifree.com`).
- Compatibilité locale conservée avec `diddishop-system@diddifree.com` lorsque
  le service de test n’a pas de téléphone ; le staging refuse toujours cette
  configuration avant démarrage.
- Documentation et décision D-061 ajoutées.
- Vérification : `pytest tests/test_contract_wiring.py tests/test_configuration.py -q`
  → 8 passed.

La suite complète après le fallback email : `239 passed`.

## Déploiement

Déploiement manuel Portainer en attente de l’injection des deux valeurs réelles
du sender technique. Aucun déploiement n’a été effectué par l’agent.
