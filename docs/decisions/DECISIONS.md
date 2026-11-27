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

### D-023 — Portail documentaire statique séparé
- Date : 2026-11-25
- Phase / sous-lot : S14 — publication documentaire
- Décision : publier la documentation MkDocs dans un conteneur Nginx statique séparé de l’API, activé explicitement en staging par `DOCS_PUBLIC_ENABLED=true` et exposé derrière un Proxy Host HTTPS.
- Pourquoi : le frontend doit accéder à une URL publique stable sans dépendre du dépôt Git ou du poste de développement ; la documentation ne doit exposer ni secrets ni données métier.
- Alternatives écartées : servir les fichiers depuis GitHub ; monter le dossier local dans l’API ; rendre le portail public par défaut en production.
- Source : Agent, à valider
- Impact : Dockerfile.docs, Compose docs, Nginx Proxy Manager, MkDocs, DNS/TLS staging.

### D-024 — Stack Portainer unifiée pour l’API et MkDocs
- Date : 2026-11-25
- Phase / sous-lot : S15-A — alignement de l’infrastructure documentaire DiddiGo
- Décision : fournir `docker-compose.portainer.yml` avec les services API et docs dans la même stack, construits depuis le même checkout Git. Le portail MkDocs est activé explicitement en staging par `DOCS_PUBLIC_ENABLED=true` et reste accessible à Nginx Proxy Manager par un port hôte configurable lorsque le réseau Docker partagé n’est pas disponible.
- Pourquoi : reproduire le modèle DiddiGo observé et garantir que l’URL publique documente la même révision que l’API déployée.
- Alternatives écartées : déployer MkDocs dans une stack indépendante non synchronisée ; servir les Markdown depuis Git ou le poste du développeur ; imposer un réseau Docker NPM indisponible.
- Source : DiddiGo `docker-compose.portainer.yml` et `docs/configuration/DOCUMENTATION_PORTAL.md` ; Agent, à valider
- Impact : Portainer, Docker Compose, MkDocs, Nginx Proxy Manager, DNS/TLS staging.

### D-025 — Environnement Portainer séparé des secrets versionnés
- Date : 2026-11-25
- Phase / sous-lot : S15-D — variables de déploiement Portainer
- Décision : fournir `portainer.env.example` versionné avec les URLs staging et la forme des variables, tandis que `portainer.env` opérationnel reste ignoré par Git et chargé dans Portainer après remplacement des secrets provisionnés.
- Pourquoi : donner un fichier directement exploitable sans publier les mots de passe PostgreSQL, secrets clients DiddiFreeID, signatures webhook ou credential OTEL.
- Alternatives écartées : committer des secrets réels ; inventer des credentials ; laisser Portainer déduire des variables non déclarées par Compose.
- Source : Agent, à valider
- Impact : Portainer, Docker Compose, DiddiFreeID, DiddiPay, DiddiSend, DiddiObserve.

### D-026 — Documentation dans la stack Compose principale
- Date : 2026-11-26
- Phase / sous-lot : S15-E — alignement de la stack réellement déployée
- Décision : inclure le service `docs` directement dans `docker-compose.yml`, en plus du fichier Portainer dédié, afin que le déploiement Compose par défaut de DiddiShop publie aussi MkDocs dans la même stack que l’API.
- Pourquoi : éviter qu’un déploiement Portainer sélectionnant le fichier Compose principal oublie le portail documentaire ; conserver l’URL frontend découplée du Git et du poste local.
- Alternatives écartées : dépendre uniquement du fichier `docker-compose.portainer.yml` ; laisser Portainer déployer une stack API sans documentation.
- Source : Utilisateur, à valider
- Impact : Docker Compose, Portainer, MkDocs, Nginx Proxy Manager, frontend.

### D-027 — Surface frontend V1 et contrats de réponse stables
- Date : 2026-11-26
- Phase / sous-lot : S16 — complétion du parcours frontend MVP
- Décision : exposer les listes catalogue/boutique, les espaces vendeur, la suppression de ligne panier, les listes de commandes, le parcours photo DiddiFiles et un checkout contenant une section `payment` normalisée ; les erreurs exposent un code stable indépendant du texte.
- Pourquoi : le MVP doit être utilisable par l’application sans connaître des identifiants préalables ni interpréter des messages libres.
- Alternatives écartées : laisser le frontend composer des lectures unitaires ; renvoyer les dataclasses internes ; transmettre la réponse DiddiPay complète ; piloter les erreurs par le texte.
- Source : Utilisateur, à valider
- Impact : catalog, shops, cart, checkout, orders, DiddiFiles, OpenAPI et frontend.

### D-028 — Allow-list CORS frontend
- Date : 2026-11-26
- Phase / sous-lot : S17-A
- Décision : autoriser les origines HTTP/HTTPS des sous-domaines `*.diddifree.com`
  et `localhost` avec port optionnel ; autoriser méthodes et headers frontend,
  dont `Authorization`, sans credentials navigateur.
- Pourquoi : le frontend est servi depuis une origine distincte et doit pouvoir
  exécuter les appels API navigateur ; une allow-list est préférable à `*`.
- Alternatives écartées : `allow_origins=["*"]` ; autoriser toutes les origines ;
  activer les cookies cross-site.
- Source : Utilisateur | Agent
- Impact : `app_base/main.py`, tests HTTP, documentation API et déploiement.

### D-029 — Contrats frontend et catégories V1
- Date : 2026-11-26
- Phase / sous-lot : S18-A/B — contrats de réponse et documentation
- Décision : publier des schémas OpenAPI explicites pour les ressources frontend
  et fournir `GET /v1/catalog/categories` avec des codes stables (`fashion`,
  `beauty`, `home`, `electronics`, `food`, `books`, `sports`, `services`,
  `other`). Les valeurs restent acceptées comme texte pour compatibilité, mais
  le frontend utilise les codes de cette liste.
- Pourquoi : l’application doit pouvoir construire ses écrans sans deviner la
  forme des réponses ni maintenir une taxonomie divergente.
- Alternatives écartées : laisser OpenAPI sans schémas ; inventer des catégories
  côté frontend ; rendre la catégorie obligatoire avant migration des données.
- Source : Utilisateur | Agent, à valider
- Impact : catalogue, OpenAPI, MkDocs, frontend, tests de contrat.

### D-030 — Confirmation DiddiFiles médiée par DiddiShop
- Date : 2026-11-26
- Phase / sous-lot : S18-C — contrat médias
- Décision : après l’upload PUT de l’application vers l’URL signée, l’application
  appelle la route d’attachement DiddiShop ; DiddiShop confirme le fichier auprès
  de DiddiFiles, valide son usage produit, puis rattache le fichier au produit.
- Pourquoi : centraliser l’autorisation métier et empêcher un rattachement d’un
  fichier non confirmé ou destiné à un autre module.
- Alternatives écartées : laisser l’application confirmer directement puis
  considérer le fichier comme rattaché ; accepter uniquement un `file_id` sans
  contrôle de statut/purpose.
- Source : Contrat DiddiFiles staging vérifié le 2026-11-26 | Agent, à valider
- Impact : catalogue, DiddiFiles, frontend, sécurité S2S.

### D-031 — Déclenchement DiddiSend par DiddiShop après signal vendeur
- Date : 2026-11-26
- Phase / sous-lot : S19-A — orchestration prête à expédier
- Décision : l’application vendeur appelle uniquement
  `POST /v1/orders/{order_id}/ready`. DiddiShop valide la transition vers
  `READY_FOR_PICKUP`, appelle immédiatement DiddiSend avec la clé
  `shop:create-delivery:{order_id}:1` et persiste la projection de livraison.
- Pourquoi : reproduire le parcours DiddiFood et garder l’autorité de la
  création d’expédition, de l’idempotence et de l’intégration S2S dans le
  backend DiddiShop.
- Alternatives écartées : laisser le frontend appeler DiddiSend ; créer la
  livraison avant la transition locale ; exiger un second clic opérationnel.
- Source : Utilisateur | Agent, à valider
- Impact : commandes, DiddiSend, projection livraison, API vendeur, MkDocs.

### D-032 — Transparence de couverture documentaire
- Date : 2026-11-26
- Phase / sous-lot : S20-A/B/C — audit MkDocs API et protocoles
- Décision : MkDocs doit distinguer l’inventaire exhaustif des routes de la
  complétude de leurs schémas. Les routes sans modèle de réponse explicite sont
  marquées `à typer`. L’absence de WebSocket est documentée ; REST/JSON,
  webhooks, S2S et OTLP sont les seuls protocoles annoncés.
- Pourquoi : éviter que la présence d’une route dans OpenAPI soit interprétée
  comme un contrat frontend complet.
- Alternatives écartées : déclarer tous les contrats complets sur la base de
  réponses génériques ; laisser le frontend déduire les valeurs ; annoncer un
  WebSocket non implémenté.
- Source : Utilisateur | Agent, à valider
- Impact : MkDocs, OpenAPI, frontend, intégrations et backlog de contrats.

### D-033 — Référence route par route
- Date : 2026-11-26
- Phase / sous-lot : S21-A/B/C — documentation opérationnelle API
- Décision : chaque route métier doit avoir dans MkDocs sa méthode, son niveau
  d’authentification, ses paramètres, contraintes, payload, réponse, erreurs,
  valeurs et limites. Une garantie absente du code est marquée `à compléter`
  ou `à corriger`, jamais présentée comme disponible.
- Pourquoi : l’OpenAPI peut confirmer la présence d’une route sans expliquer
  suffisamment son comportement à une équipe frontend ou à un intégrateur S2S.
- Alternatives écartées : renvoyer uniquement vers `openapi.json` ; documenter
  seulement les happy paths ; masquer les protections d’acteur manquantes.
- Source : Utilisateur | Agent, à valider
- Impact : MkDocs, frontend, backend, sécurité, intégrations et recette staging.

### D-034 — Complétion des contrats transactionnels frontend V1
- Date : 2026-11-26
- Phase / sous-lot : S22-A/B/C
- Décision : implémenter dans l’API les contrats manquants plutôt que les
  laisser uniquement dans MkDocs : panier enrichi, devis checkout, lecture et
  reprise de paiement, lignes de commande, projection DiddiSend détaillée,
  erreurs d’annulation et transitions produit pause/retrait.
- Pourquoi : le frontend doit pouvoir exécuter le parcours MVP avec des
  réponses typées et des règles déterministes, sans calculer les montants ni
  inventer les statuts.
- Alternatives écartées : documenter les trous sans code ; laisser le
  frontend calculer les frais ; exposer des réponses internes non typées.
- Source : Utilisateur | Agent, à valider
- Impact : panier, checkout, DiddiPay, commandes, DiddiSend, claims, catalogue,
  OpenAPI, MkDocs et tests.

### D-035 — Idempotence des créations et reprises de paiement
- Date : 2026-11-26
- Phase / sous-lot : S22-B
- Décision : `POST /v1/checkouts` mémorise la réponse par
  `Idempotency-Key` et empreinte du client + corps ; une clé réutilisée avec un
  autre corps renvoie un conflit. `/retry` applique la même règle dans un
  périmètre séparé et n’accepte qu’un checkout `payment_failed`.
- Pourquoi : empêcher la création de plusieurs commandes ou PaymentIntents
  lors d’un timeout réseau ou d’un double clic.
- Alternatives écartées : compter uniquement sur le frontend ; réutiliser une
  clé de création pour une reprise ; ignorer le corps original.
- Source : Agent, à valider
- Impact : checkout, idempotence SQL/Redis, DiddiPay, OpenAPI et frontend.

### D-036 — Contrat paiement frontend V1
- Date : 2026-11-26
- Phase / sous-lot : S23-B
- Décision : le frontend choisit `wave`, `mtn_momo` ou `orange_money`, avec
  `wave` par défaut. Une `return_url` facultative est acceptée uniquement vers
  `diddifree.com` ou `localhost`. La réponse expose seulement les champs
  DiddiPay nécessaires : identifiant, montant XOF, statut, moyen et expiration.
- Pourquoi : rendre le parcours mobile money déterministe sans exposer de
  token, secret ou URL de redirection arbitraire.
- Alternatives écartées : accepter une URL quelconque ; exposer la réponse
  DiddiPay brute ; inventer un champ obligatoire non publié par staging.
- Source : Agent, à valider
- Impact : checkout, DiddiPay, sécurité, frontend et OpenAPI.

### D-037 — Pagination et historique des commandes
- Date : 2026-11-26
- Phase / sous-lot : S23-B
- Décision : `GET /v1/orders` utilise `limit` (1–100, défaut 20) et un curseur
  opaque ; chaque commande expose `created_at`, `delivered_at` et un
  `status_history` horodaté.
- Pourquoi : éviter un contrat qui ne passe pas à l’échelle et permettre au
  frontend d’afficher l’heure de chaque étape sans reconstruire l’historique.
- Alternatives écartées : pagination par numéro de page ; timestamps calculés
  côté client ; exposer les événements internes complets.
- Source : Agent, à valider
- Impact : commandes, persistance payload, OpenAPI et frontend.

### D-038 — Réclamations et preuves V1
- Date : 2026-11-26
- Phase / sous-lot : S23-C
- Décision : ajouter la lecture par commande, calculer `claim_deadline` à
  `delivered_at + 72h`, utiliser des motifs contrôlés, accepter au maximum
  trois photos DiddiFiles et retourner un remboursement avec moyen et
  référence masquée, sans numéro de téléphone complet.
- Pourquoi : permettre le suivi du dossier dans l’application tout en
  limitant les données sensibles et les variations de motifs.
- Alternatives écartées : laisser le motif entièrement libre ; exposer le
  numéro de paiement complet ; stocker les preuves dans DiddiShop.
- Source : Agent, à valider
- Impact : claims, DiddiFiles, DiddiPay, support, OpenAPI et frontend.

### D-039 — Projection de suivi DiddiSend
- Date : 2026-11-26
- Phase / sous-lot : S23-D
- Décision : normaliser `courier` en `id/name/phone_masked/avatar_url/vehicle_type`
  et `position` en `latitude/longitude/updated_at`, tout en gardant DiddiSend
  comme source de vérité.
- Pourquoi : fournir un contrat stable pour la fiche coursier et la carte sans
  coupler le frontend aux variantes de payload du transporteur.
- Alternatives écartées : renvoyer le payload DiddiSend brut ; laisser le
  frontend gérer `lat/lng` et tous les alias ; dupliquer la vérité logistique.
- Source : Agent, à valider
- Impact : delivery, DiddiSend, commandes, OpenAPI et frontend.

### D-040 — Injection Portainer des paramètres d’exécution
- Date : 2026-11-26
- Phase / sous-lot : S24-A
- Décision : le Compose Portainer transmet explicitement les URLs des services,
  les clients S2S, les secrets de webhook, les paramètres de délais/finance et
  les marqueurs OTEL. Les valeurs sensibles restent injectées par Portainer
  ou le secret manager et ne sont jamais commitées.
- Pourquoi : une variable présente dans `portainer.env.example` mais non
  transmise au conteneur est silencieusement ignorée par l’application.
- Alternatives écartées : dépendre de variables implicites du shell ; mettre
  des secrets dans le dépôt ; réutiliser un seul credential S2S.
- Source : Utilisateur | Agent, à valider
- Impact : Portainer, Compose, DiddiFreeID, DiddiPay, DiddiSend,
  DiddiObserve et paramètres métier.

### D-041 — Compose canonique Portainer
- Date : 2026-11-26
- Phase / sous-lot : S24-B
- Décision : conserver `docker-compose.yml` comme fichier configuré par la
  stack Portainer existante, y déplacer le Compose staging complet, et créer
  `docker-compose.local.yml` pour le développement local.
- Pourquoi : la stack existante pointe déjà vers `docker-compose.yml` ; changer
  son nom de fichier aurait nécessité une reconfiguration de stack et pouvait
  laisser le déploiement sur l’ancien Compose sans toutes les variables.
- Alternatives écartées : modifier manuellement la stack Portainer ; conserver
  deux Compose staging concurrents ; laisser le fichier par défaut en mode
  développement.
- Source : Utilisateur | Agent, à valider
- Impact : Portainer, Docker Compose, documentation, déploiement staging et
  développement local.

### D-042 — Contrat réel du callback DiddiPay
- Date : 2026-11-26
- Phase / sous-lot : S24-C
- Décision : utiliser `DIDDI_SHOP_DIDDIPAY_WEBHOOK_SECRET` uniquement pour
  vérifier le HMAC-SHA256 entrant dans `X-DiddiPay-Signature`, sur le corps JSON
  exact envoyé par DiddiPay et sans timestamp. Adapter l’enveloppe DiddiPay
  `{id, type, occurred_at, data}` vers `ExternalEvent`, en résolvant le checkout
  depuis `data.checkout_id` ou `data.business_reference`.
- Pourquoi : `PAYMENT_CALLBACK_TARGETS` configure le secret côté DiddiPay et
  DiddiPay ne signe pas avec le credential S2S utilisé par DiddiShop pour ses
  appels sortants.
- Alternatives écartées : utiliser `X-Webhook-Signature`, signer un corps
  re-sérialisé côté Shop, ou réutiliser le secret client S2S.
- Source : Utilisateur | code DiddiPay cité par l’utilisateur | Agent
- Impact : webhook DiddiPay, configuration, checkout, commandes, inbox,
  sécurité, tests et documentation.

### D-043 — Scope exact des opérations DiddiSend
- Date : 2026-11-26
- Phase / sous-lot : S24-D
- Décision : demander `diddisend:deliveries:create` pour la création d’une
  livraison, avec `quote`, `read` et `cancel` pour les opérations associées.
  Ne plus demander `diddisend:deliveries:write`.
- Pourquoi : le code DiddiSend staging expose la permission de création sous
  `create`; `write` n’est pas le scope vérifié par sa politique de livraison.
- Alternatives écartées : conserver un scope générique `write` ; réutiliser le
  credential DiddiFood ; désactiver l’authentification staging.
- Source : code DiddiSend staging audité | Agent, à valider
- Impact : DiddiFreeID, DiddiShop, DiddiSend, configuration Portainer et
  recette E2E.

### D-044 — Identité S2S et callback DiddiSend
- Date : 2026-11-26
- Phase / sous-lot : S24-D
- Décision : utiliser le client explicite `diddishop-staging-diddisend` avec
  audience `diddisend`, origine `diddishop` et UUID technique dédié pour
  `X-User-ID` et `sender_user_id`. DiddiShop accepte les callbacks DiddiSend
  signés par `X-DiddiSend-Signature` au format `sha256=<digest>` et utilise un
  secret HMAC entrant distinct du secret client S2S.
- Pourquoi : le contrat DiddiSend transmis par l’équipe impose une identité
  par cible et sépare l’authentification sortante de la signature des
  événements entrants.
- Alternatives écartées : réutiliser `service_client_id` global ; envoyer
  l’UUID du vendeur comme sender technique ; réutiliser le secret DiddiPay ou
  le secret client pour les callbacks.
- Source : Utilisateur | Agent, à valider
- Impact : configuration, Compose, DiddiFreeID, DiddiSend, checkout,
  webhooks, tests et documentation.

### D-045 — Chargement compatible des clés JWT
- Date : 2026-11-27
- Phase / sous-lot : S24-E
- Décision : charger les clés JWKS avec `PyJWK.from_dict` et vérifier cette
  dépendance pendant la construction Docker.
- Pourquoi : l’image staging échouait sur `jwt.algorithms.RSAAlgorithm`, alors
  que PyJWT récent expose le chemin stable `PyJWK`.
- Alternatives écartées : désactiver la vérification JWT ; accepter un JWT
  sans signature ; modifier le contrat frontend ou DiddiSend.
- Source : incident staging | Agent, à valider
- Impact : authentification DiddiFreeID, image API, panier, checkout et tests.

### D-046 — Audience distincte pour JWT utilisateur et S2S
- Date : 2026-11-27
- Phase / sous-lot : S24-F
- Décision : ne pas exiger `aud` sur les JWT utilisateurs DiddiFreeID, car le
  contrat staging actuel fournit `iss=diddifree-id`, `sub` et `exp` sans claim
  `aud`. Exiger `aud=diddishop` sur les routes internes S2S. Rendre l’issuer
  `diddifree-id` obligatoire en staging.
- Pourquoi : la vérification frontend était incompatible avec les tokens
  réellement émis et le Compose remettait `diddishop` par défaut même quand
  l’audience était laissée vide.
- Alternatives écartées : ajouter artificiellement `X-Actor-ID`, désactiver
  toute validation d’issuer, ou modifier le token utilisateur sans contrat
  confirmé de DiddiFreeID.
- Source : incident staging et JWT observé par l’utilisateur | Agent
- Impact : authentification frontend, routes internes, Compose, configuration
  Portainer et tests.

### D-047 — Migrations avant démarrage de l’API staging
- Date : 2026-11-27
- Phase / sous-lot : S24-G
- Décision : le service API du Compose staging exécute `alembic upgrade head`
  puis démarre Uvicorn avec `exec`. Les migrations restent dans l’image et la
  base PostgreSQL conserve son volume persistant.
- Pourquoi : les migrations `0001` et `0002` existaient déjà, mais aucune
  commande ne les exécutait au démarrage ; la table `carts` manquait en staging.
  Ce modèle suit DiddiFood staging et le runner de démarrage des autres modules.
- Alternatives écartées : appliquer les migrations manuellement après chaque
  déploiement ; utiliser `Base.metadata.create_all()` ; modifier la base
  directement sans migration versionnée.
- Source : incident staging et comparaison DiddiFood/DiddiPay/DiddiSupport | Agent
- Impact : Dockerfile/Compose staging, démarrage API, PostgreSQL, runbook et tests.

### D-048 — Réhydrater les enums produit depuis PostgreSQL
- Date : 2026-11-27
- Phase / sous-lot : S24-H
- Décision : convertir `payload.status` en `ProductStatus` dans le repository
  SQL avant de reconstruire un `Product`.
- Pourquoi : la persistance JSON stocke correctement la valeur texte, mais les
  services panier et checkout utilisent ensuite l’API enum `.value`.
- Alternatives écartées : comparer partout des chaînes ; modifier le schéma
  SQL ; supprimer l’usage de l’enum du domaine.
- Source : erreur runtime staging `str has no attribute value` | Agent
- Impact : repository produit, panier, checkout et tests SQL.

### D-049 — Normaliser les réponses de devis DiddiSend
- Date : 2026-11-27
- Phase / sous-lot : S24-I
- Décision : accepter les montants numériques et les objets de devis contenant
  `amount_minor`, `quoted_price`, `delivery_fee`, `amount` ou `value`, puis
  retourner un montant entier XOF au domaine.
- Pourquoi : DiddiSend a renvoyé `quote` comme objet ; la conversion directe
  en entier provoquait HTTP 500. Les erreurs upstream de devis deviennent un
  502 métier explicite.
- Alternatives écartées : convertir aveuglément le dictionnaire en chaîne ;
  laisser l’exception Python remonter ; accepter silencieusement un montant nul.
- Source : traces Grafana/Portainer et contrat DiddiSend | Agent
- Impact : adaptateur DiddiSend, checkout, erreurs API et tests d’intégration.

### D-050 — Mapper le paiement Shop vers le contrat DiddiPay PaymentIntent
- Date : 2026-11-27
- Phase / sous-lot : S24-J
- Décision : envoyer `channel=mobile_money` et mapper `wave` vers `network=wave`,
  `mtn_momo` vers `network=mtn` et `orange_money` vers `network=orange`.
  Ne plus envoyer `payment_method` ni `return_url`.
- Pourquoi : le schéma staging DiddiPay expose `channel`/`network` et rejette
  les propriétés supplémentaires ; `return_url` n’est pas un champ accepté.
- Alternatives écartées : ajouter un support `cash` ; transmettre les champs
  Shop tels quels ; supprimer le moyen de paiement mobile money.
- Source : OpenAPI DiddiPay staging vérifiée le 2026-11-27 | Agent
- Impact : adaptateur DiddiPay, checkout, tests et documentation d’intégration.

### D-051 — Persister l’échec du PaymentIntent dans le checkout
- Date : 2026-11-27
- Phase / sous-lot : S24-K
- Décision : un résultat DiddiPay `status=failed` met immédiatement le checkout
  à `payment_failed` et persiste `payment_failure_code`,
  `payment_failure_message` et `payment_provider_status`. Le retry exige une
  nouvelle clé d’idempotence, sauvegarde d’abord `payment_pending`, puis
  conserve le résultat `payment_failed` ou `payment_succeeded`.
- Pourquoi : le checkout ne doit pas rester `payment_pending` après un échec
  terminal du PaymentIntent ; sinon la route retry refuse à tort la reprise.
- Alternatives écartées : déduire l’échec uniquement depuis un webhook futur ;
  autoriser le retry depuis `payment_pending` ; réutiliser la même clé.
- Source : incident staging et contrat DiddiPay | Utilisateur / Agent
- Impact : checkout application service, réponse API, persistance et retry.

### D-052 — Transmettre le téléphone client au PaymentIntent
- Date : 2026-11-27
- Phase / sous-lot : S24-L
- Décision : ajouter `customer_phone` au contrat interne PaymentIntent et le
  transmettre à DiddiPay dans le payload. Le checkout le conserve dans son
  résultat de paiement afin que les retries réutilisent le même téléphone.
- Pourquoi : PawaPay exige `customer_phone` pour un dépôt mobile money ; le
  checkout possédait déjà la valeur validée dans `recipient_phone`.
- Alternatives écartées : réutiliser `recipient_phone` comme nom externe ;
  demander au frontend de répéter le téléphone lors du retry ; modifier
  DiddiPay/PawaPay.
- Source : erreur staging `customer_phone is required by pawapay deposits` |
  Utilisateur / Agent
- Impact : contrat PaymentIntent, adaptateur DiddiPay, checkout et retries.
