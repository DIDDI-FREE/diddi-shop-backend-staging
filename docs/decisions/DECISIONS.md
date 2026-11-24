# DiddiShop — décisions d’architecture

Les décisions existantes sont conservées ici avant le démarrage de la boucle
d’implémentation. Une décision ne sera jamais modifiée silencieusement ; une
nouvelle décision la remplacera explicitement si nécessaire.

### D-001 — Monolithe modulaire Clean Architecture
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0
- Décision : DiddiShop démarre comme un monolithe modulaire organisé en domain, application, infrastructure et présentation.
- Pourquoi : réduire le coût opérationnel du MVP tout en conservant des frontières extractibles.
- Alternatives écartées : microservices séparés dès le premier déploiement.
- Source : Plan / `ARCHITECTURE_SKELETON.md`
- Impact : tous les modules.

### D-002 — DiddiSend est l’unique frontière d’expédition
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0
- Décision : DiddiShop appelle uniquement DiddiSend pour devis, création, suivi et annulation de livraison.
- Pourquoi : DiddiShop ne possède ni flotte, ni coursier, ni orchestration logistique.
- Alternatives écartées : appel direct à un service de flotte ou à un autre module logistique.
- Source : Utilisateur / Plan
- Impact : checkout, orders, intégration DiddiSend.

### D-003 — DiddiPay reste propriétaire du paiement et de la comptabilité
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0
- Décision : DiddiShop conserve les références, snapshots et statuts synchronisés, mais ne stocke pas les données de carte et ne recalcule pas la comptabilité DiddiPay.
- Pourquoi : séparer la décision métier de la tenue financière.
- Alternatives écartées : wallet ou ledger financier local dans DiddiShop.
- Source : Plan / spécification MVP §2, §6
- Impact : checkout, finance, claims.

### D-004 — Commande et paiement sont deux axes séparés
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0
- Décision : conserver `fulfillment_status` et `payment_status` séparément.
- Pourquoi : une livraison, un remboursement et une release ne doivent pas réécrire le même historique.
- Alternatives écartées : statut unique de commande.
- Source : Spécification MVP §3
- Impact : orders, webhooks, claims, finance.

### D-005 — Montants entiers en XAF et snapshots financiers
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0
- Décision : tous les montants métier sont des entiers CFA et les prix, frais, commission et paramètres sont figés à la validation.
- Pourquoi : éviter les recalculs divergents et les erreurs d’arrondi.
- Alternatives écartées : recalcul à partir du catalogue courant ; montants flottants.
- Source : Spécification MVP §2 et §6
- Impact : catalog, checkout, orders, finance.

### D-006 — Stock non réservé dans le panier
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0
- Décision : le stock est décrémenté atomiquement au checkout et restitué au maximum une fois.
- Pourquoi : simplifier le MVP et concentrer la concurrence sur une transaction de validation.
- Alternatives écartées : réservation temporaire dans le panier.
- Source : Spécification MVP §1.3
- Impact : cart, checkout, catalog.

### D-007 — Outbox/inbox et idempotence obligatoires
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0
- Décision : les changements métier et événements sortants sont transactionnels ; les événements entrants sont dédupliqués par consommateur et `event_id`.
- Pourquoi : les services externes et workers sont au minimum at-least-once.
- Alternatives écartées : appels synchrones sans journalisation ; déduplication en mémoire.
- Source : Spécification MVP §4 et §5
- Impact : tous les modules transactionnels et workers.

### D-008 — Rewards/campagnes restent la propriété de DiddiRewards
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0
- Décision : DiddiShop consomme quote/reserve/consume/release et projette les campagnes utiles ; il ne possède ni budget, ni ledger, ni moteur de campagne.
- Pourquoi : éviter un deuxième moteur Rewards dans le marketplace.
- Alternatives écartées : promotions et coupons locaux dans DiddiShop.
- Source : Plan §2 et `INTEGRATION_MAP.md`
- Impact : checkout, order snapshots, rewards, campaigns.

### D-009 — Support et backoffice passent par des use cases audités
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0
- Décision : Support et DiddiBackoffice n’écrivent jamais directement dans les tables DiddiShop ; ils appellent des routes/use cases idempotents avec acteur, motif et corrélation.
- Pourquoi : préserver les invariants et l’audit.
- Alternatives écartées : accès direct à la base ou mutation ad hoc.
- Source : Plan §P6, §P7 et `CAPABILITY-MAP.md`
- Impact : claims, orders, admin, audit.

### D-010 — Contrats externes non confirmés derrière des ports
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0
- Décision : implémenter les ports et faux adaptateurs testés tant que les contrats DiddiPay, DiddiSend, DiddiFiles et DiddiFreeID ne sont pas confirmés.
- Pourquoi : continuer sans inventer un contrat financier ou S2S irréversible.
- Alternatives écartées : intégrer directement des routes supposées.
- Source : Plan §9 / Mission §5
- Impact : integrations, checkout, delivery, finance, security.

### D-011 — Release vendeur derrière un port abstrait
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0 → P6-D
- Décision : implémenter `SellerReleasePort` et un faux adaptateur testé ; conserver `RELEASE_PENDING` tant que le contrat marketplace DiddiPay n’est pas confirmé.
- Pourquoi : avancer sur les invariants et la finance métier sans inventer une opération de transfert d’argent.
- Alternatives écartées : bloquer toute la phase finance ; appeler le payout DiddiPay comme s’il s’agissait d’une release marketplace.
- Source : Agent, à valider / réponse utilisateur Q1
- Impact : finance, claims, orders, intégration DiddiPay.

### D-012 — Adaptateur DiddiSend calqué sur DiddiFood
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0 → P2-B / P5-B
- Décision : DiddiShop utilisera un `DeliveryGateway`/`DiddiSendAdapter` avec credential S2S, `X-Origin-Service`, `X-User-ID`, `Idempotency-Key`, `origin_module=diddishop`, `order_reference` et breakdown financier figé.
- Pourquoi : reprendre le contrat d’intégration réellement utilisé par DiddiFood, sans coupler DiddiShop aux détails internes de flotte.
- Alternatives écartées : créer un client DiddiGo ; envoyer uniquement un `order_id` sans payload métier ; faire payer DiddiSend une seconde fois.
- Source : Utilisateur / inspection de `diddi-food/app/modules/delivery/infra/diddisend_adapter.py`
- Impact : checkout, orders, delivery adapter, finance.

### D-013 — PostgreSQL et Redis
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0 → P1-B / P1-C
- Décision : utiliser PostgreSQL pour les agrégats et transactions, Redis pour outbox/inbox, verrous et workers.
- Pourquoi : répondre au plan de production et gérer les traitements at-least-once.
- Alternatives écartées : SQLite de production ; PostgreSQL seul en polling pour le MVP.
- Source : Utilisateur
- Impact : platform-runtime, persistence, workers, idempotence.

### D-014 — Scopes S2S dédiés par service
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0 → P2-A / P2-B / P2-C
- Décision : utiliser des clients et scopes DiddiFreeID distincts pour chaque service appelé par DiddiShop.
- Pourquoi : appliquer le modèle des autres modules métier et limiter le blast radius d’un credential.
- Alternatives écartées : clé globale partagée ; fallback permanent legacy.
- Source : Utilisateur
- Impact : auth, integrations, configuration, déploiement.

### D-015 — Initialisation du dépôt Git
- Date : 2026-11-24
- Phase / sous-lot : PHASE 0
- Décision : initialiser le dépôt local, créer `main`, ajouter le remote GitHub fourni et pousser l’état initial.
- Pourquoi : permettre les commits dédiés exigés par la mission.
- Alternatives écartées : continuer sans historique ; utiliser un remote différent.
- Source : Utilisateur
- Impact : suivi, commits, livraison.

### D-016 — DiddiSend possède la validation opérationnelle de livraison
- Date : 2026-11-24
- Phase / sous-lot : suite d’implémentation — cadrage staging
- Décision : DiddiShop ne dépend pas de DiddiMap. DiddiSend reçoit les adresses de retrait et de destination, applique ses propres règles de validation opérationnelle et reste propriétaire de l’expédition.
- Pourquoi : éviter une dépendance supplémentaire et conserver une seule frontière logistique pour le marketplace.
- Alternatives écartées : ajouter DiddiMap au checkout ; géocoder ou valider localement dans DiddiShop.
- Source : Utilisateur
- Impact : configuration, checkout, intégration DiddiSend, documentation des contrats.

### D-017 — Séquestration et release vendeur reportées en V2
- Date : 2026-11-24
- Phase / sous-lot : suite d’implémentation — cadrage MVP/V2
- Décision : le MVP V1 ne séquestre pas les fonds et ne déclenche aucune release vendeur. DiddiPay couvre le paiement client, les annulations et les remboursements. La séquestration marketplace, l’éligibilité après délai et la release vendeur sont reportées en V2.
- Pourquoi : réduire le périmètre financier du MVP et éviter d’activer un flux marketplace tant que son contrat DiddiPay n’est pas formellement disponible.
- Alternatives écartées : utiliser le payout générique comme release ; conserver une release simulée en production ; bloquer le checkout en attendant la V2.
- Source : Utilisateur
- Impact : finance, commandes, DiddiPay, scopes S2S, backoffice, documentation MVP/V2.

### D-018 — Tokens S2S dynamiques par service cible
- Date : 2026-11-24
- Phase / sous-lot : S9-A — authentification sortante DiddiFreeID
- Décision : chaque cible externe utilise un `client_id` et un `client_secret` DiddiFreeID distincts ; DiddiShop obtient un token via `client_credentials`, avec l’audience et les scopes de la cible, puis le met en cache jusqu’à expiration.
- Pourquoi : respecter l’isolation des scopes et éviter les tokens statiques partagés entre services.
- Alternatives écartées : un `service_client_id` global ; tokens statiques en staging/production ; transmettre les scopes uniquement dans un header sans les porter dans le JWT.
- Source : Utilisateur et contrat `SERVICE_TOKEN_CONTRACT.md`
- Impact : settings, registre d’intégrations, DiddiFreeID, tous les adaptateurs S2S, déploiement secret manager.

### D-019 — DiddiComms conversation distincte des notifications
- Date : 2026-11-24
- Phase / sous-lot : S10-A — correction du contrat DiddiComms
- Décision : DiddiShop utilise la route DiddiComms uniquement pour ouvrir ou retrouver une conversation rattachée à une tâche métier. L’appel ne contient aucun body JSON et ne déclenche pas de SMS, WhatsApp ou notification.
- Pourquoi : l’OpenAPI staging vérifiée indique que la route reçoit `owner_service`, `task_type` et `task_id` dans l’URL et ne publie pas de contrat d’envoi événementiel.
- Alternatives écartées : conserver `create_task` avec payload JSON ; déduire un envoi à partir d’un événement Shop ; traiter `Idempotency-Key` comme une garantie de livraison par canal.
- Source : équipe DiddiComms / OpenAPI staging
- Impact : intégration DiddiComms, module communication, scopes S2S à confirmer, documentation des événements.

### D-020 — Devise unique XOF pour DiddiFree
- Date : 2026-11-24
- Phase / sous-lot : S11-A — alignement DiddiRewards
- Décision : tous les montants et contrats financiers DiddiShop utilisent exclusivement XOF. Aucune conversion XAF/XOF ne doit être ajoutée, même si une ancienne documentation ou une instruction ultérieure mentionne XAF.
- Pourquoi : DiddiRewards et les contrats interservices DiddiFree sont exprimés en XOF ; une conversion implicite créerait une incohérence financière non traçable.
- Alternatives écartées : conserver XAF côté Shop ; convertir automatiquement entre XAF et XOF ; accepter une devise variable par intégration.
- Source : Utilisateur
- Impact : catalogue, checkout, commandes, DiddiPay, DiddiSend, DiddiRewards, tests et documentation.
- Remplace : D-005 pour la devise.

## Décisions agent à valider

Les décisions agent à valider sont conservées explicitement dans cette section.

### D-021 — DiddiObserve hors S2S métier
- Date : 2026-11-24
- Phase / sous-lot : S12-A à S12-C
- Décision : utiliser exclusivement OTLP HTTP/protobuf avec le Basic credential dédié fourni hors Git ; ne pas provisionner ni réutiliser de client/scope DiddiFreeID pour DiddiObserve.
- Pourquoi : la remise plateforme confirme une authentification d’observabilité dédiée et précise qu’aucun scope OAuth/S2S métier n’est requis.
- Alternatives écartées : réutiliser le client `diddiobserve` dans la map S2S ; envoyer du JSON applicatif ; committer le secret d’onboarding.
- Source : Utilisateur / remise DiddiShop du 2026-11-24
- Impact : settings, telemetry, intégration DiddiObserve, Compose, déploiement.

### D-022 — Scrape Prometheus différé
- Date : 2026-11-24
- Phase / sous-lot : S12-D
- Décision : ne pas activer le scrape DiddiShop tant que la plateforme n’a pas fourni et vérifié URLs, ports, chemins et `METRICS_BEARER_TOKEN` dédié.
- Pourquoi : la remise indique explicitement que les cinq scrapes existants sont UP mais que le scrape DiddiShop reste désactivé en attente des informations producteur.
- Alternatives écartées : exposer un scrape sans token ; réutiliser l’authentification OTLP ; déclarer la conformité à partir des seuls signaux synthétiques centraux.
- Source : Utilisateur / remise DiddiShop du 2026-11-24
- Impact : observabilité, déploiement, plateforme, recette staging.
