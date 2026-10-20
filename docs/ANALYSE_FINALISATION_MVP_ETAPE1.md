# Analyse de l’existant — finalisation du MVP EstuaireFleet

Date de l’audit : 20 octobre 2026
Branche auditée : `main` (`1d58b26`)

## 1. État général vérifié

Le dépôt est un projet Django organisé par domaines (`core`, `users`, `fleet`, `signals`, `alerts`, `intercampus` et `notifications`). Les domaines disposent déjà, dans l’ensemble, de modèles UUID héritant de `BaseModel`, de `TextChoices`, de selectors de lecture, de services d’écriture, de permissions, de validateurs, de tâches Celery, d’API REST et de templates server-side.

Le socle de qualité est stable au moment de l’audit :

- 29 tests passent (`pytest -q`) ;
- `ruff check .` passe ;
- `ruff format --check .` passe ;
- `manage.py check` passe ;
- `makemigrations --check --dry-run` ne détecte aucune modification de modèle ;
- la compilation Tailwind passe ;
- la branche de travail était propre avant l’audit.

La vérification des migrations a toutefois signalé que PostgreSQL local n’était pas authentifié avec les identifiants disponibles. L’absence de changement détecté par Django reste exploitable, mais une validation finale avec PostgreSQL et Redis réels est nécessaire.

## 2. Intercampus

### Déjà en place

- modèle `CoursInterCampus` avec campus de départ et d’arrivée distincts ;
- validation des horaires et de l’effectif ;
- statut métier, changement d’horaire et dates de notification ;
- affectation manuelle et automatique d’un bus avec contrôle des chevauchements ;
- notification in-app au chauffeur et rappel ;
- API CRUD et action d’affectation automatique ;
- séparation services/selectors et index sur statut/date.

### Écarts identifiés

- la tâche périodique sélectionne et compare `horaire_fin` au lieu de `start_at` pour notifier le chauffeur avant le départ ;
- l’interface staff expose la création et la confirmation, mais pas l’affectation, la modification, l’annulation, le rappel manuel ni la visibilité de l’état du chauffeur ;
- les notifications inter-campus n’utilisent pas partout le type métier dédié ;
- l’API ne propose pas d’action explicite de notification ou d’affectation manuelle ;
- la liste de gestion n’est pas paginée et la présentation reste très compacte sur mobile.

## 3. Notifications

### Déjà en place

- modèle in-app avec type, canal, statut, lecture, métadonnées et référence d’envoi ;
- selectors limités au destinataire courant ;
- marquage lu protégé par `select_for_update` ;
- endpoint de compteur non lues ;
- tâche Celery pour les canaux différés ;
- providers séparés pour l’e-mail et la structure de repli SMS.

### Écarts identifiés

- le compteur est calculé dans chaque requête et n’est pas injecté dans le shell global : aucun badge n’est visible dans la navigation ;
- les événements Signal, Alerte, réponse chauffeur, relais et escalade ne sont pas uniformément centralisés dans le système de notifications ;
- les notifications ne possèdent pas de clé d’idempotence : un retry ou deux workers peuvent produire des doublons ;
- la tâche d’envoi ne verrouille pas les lignes en attente avant dispatch ;
- les erreurs sont ignorées par la tâche sans stratégie de retry borné ni journal métier ;
- la page de liste n’est pas paginée.

## 4. Supervision Admin

### Déjà en place

- tableau de bord opérationnel avec agrégations SQL et cache court ;
- statistiques bus, étudiants, chauffeurs, signaux, alertes et incidents ;
- écrans flotte, supervision des signaux, alertes et export ;
- carte Leaflet et polling pour les signaux ou les bus ;
- permissions distinctes pour étudiant, chauffeur, personnel et administrateur.

### Écarts identifiés

- le tableau de bord n’agrège pas encore un flux unifié trajets/bus/chauffeurs/incidents ;
- la carte de supervision et les statistiques ne partagent pas de contrat de rafraîchissement ni d’indicateur d’âge des données ;
- les vues fleet historiques et les vues récentes n’ont pas la même convention visuelle ;
- certaines listes de supervision chargent des collections non paginées ;
- les permissions de lecture et la visibilité des libellés étudiants doivent être revérifiées sur chaque endpoint cartographique.

## 5. PWA

### Déjà en place

- manifest avec nom, scope, affichage standalone, couleurs de marque et URL de démarrage ;
- service worker exposé à `/sw.js`, cache shell, repli hors connexion et stratégie réseau pour les navigations ;
- enregistrement du service worker et invite d’installation ;
- métadonnées mobile et thème rouge dans le layout.

### Écarts identifiés

- les deux icônes sont des SVG malgré l’exigence d’icônes bitmap 192×192 et 512×512 minimum, et le manifest ne fournit pas de variantes PNG ;
- le cache shell référence des routes publiques et des assets sans stratégie d’invalidation fonctionnelle au-delà d’un nom de version manuel ;
- aucune vérification automatisée du manifest, du MIME type des icônes et du cache offline n’existe ;
- Flowbite est chargé depuis un CDN, ce qui réduit l’utilisabilité hors connexion ;
- le mode hors connexion est volontairement limité aux écrans shell et ne documente pas clairement les actions impossibles.

## 6. Parcours Signal → Alerte → Réponse / Escalade

### Déjà en place

- consentement, validation GPS, géorepérage et limite de tentatives ;
- contrainte d’un seul signal actif par étudiant ;
- expiration et renouvellement bornés ;
- sélection des signaux visible limitée au périmètre du chauffeur, du staff ou de l’administrateur ;
- seuil d’alerte, réponse « J’arrive », indisponibilité, relais, délai et escalade Celery ;
- plusieurs écritures sensibles sont atomiques et verrouillées.

### Risques identifiés

- l’évaluation de l’alerte et le rattachement des signaux doivent être rendus idempotents lorsque plusieurs émissions ou workers arrivent simultanément ;
- une réponse chauffeur existante est remplacée par une mise à jour de la réponse OneToOne, sans historique ni contrôle explicite de la course de relais ;
- l’escalade finale ne notifie pas systématiquement les responsables et les étudiants concernés ;
- le passage à « pris en charge » et la résolution d’alerte ne sont pas totalement unifiés : le signal peut rester actif pendant certains chemins de réponse ;
- les tâches d’expiration et d’escalade parcourent des lots sans verrouillage de sélection préalable ;
- le polling cartographique doit conserver l’interdiction pour un étudiant de voir les positions d’autres étudiants.

## 7. Performance et exploitation

Les principaux `select_related`, `prefetch_related`, index métier et le cache Redis du tableau de bord existent déjà. Les points à traiter sont la réduction des listes non paginées, le verrouillage des tâches concurrentes, la couverture de cache des lectures fréquemment rafraîchies, l’invalidation après écritures et la mesure des requêtes des écrans de supervision.

## 8. Plan de finalisation retenu

1. Finaliser les parcours et écrans inter-campus.
2. Centraliser les événements et fiabiliser les notifications avec badge, idempotence et dispatch différé.
3. Unifier la supervision administrative et son rafraîchissement.
4. Rendre la PWA installable avec de vraies icônes bitmap et un shell offline vérifiable.
5. Harmoniser l’interface mobile-first et les composants de supervision.
6. Sécuriser le flux critique par transactions, verrous, transitions explicites et notifications de bout en bout.
7. Compléter les optimisations, index, cache et tâches Celery.
8. Nettoyer puis documenter la livraison.

