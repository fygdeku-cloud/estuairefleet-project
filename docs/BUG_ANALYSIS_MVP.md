# Analyse des bugs critiques du MVP

## Périmètre et méthode

L’analyse couvre les trois parcours signalés : émission d’un signal étudiant,
lecture des notifications et supervision du dashboard. Le dépôt était propre
avant l’analyse. Les vérifications ont été faites sur les vues Django, les
services, selectors, modèles, endpoints REST, templates, JavaScript et sur la
stack Docker locale.

## 1. Signal étudiant non enregistré

### Flux observé

1. `templates/signals/home.html` attache le bouton « Je suis là » à un appel
   `navigator.geolocation.getCurrentPosition()`.
2. Le navigateur envoie ensuite `POST /api/signals/` avec `lat`, `lng` et
   `accuracy`.
3. `signals/api/views.py::SignalCollectionView` vérifie le rôle étudiant et
   appelle `signals/services.py::emit_signal`.
4. `emit_signal` verrouille le profil, vérifie le compte, le consentement,
   la suspension, le débit, le signal actif existant et le géorepérage avant
   `Signal.objects.create(...)`.

### Cause exacte

Le service respecte la règle métier du consentement, mais le parcours UI ne
permet pas de satisfaire cette règle :

- `Student.consent_location` vaut `False` par défaut;
- le formulaire d’inscription publique ne contient aucun consentement de
  géolocalisation;
- la page `signals/home.html` ne propose pas de confirmation du consentement
  avant l’appel API;
- `emit_signal` lève donc `ConsentRequired` avant la création du signal.

La réponse est bien transformée en `400` par l’API, mais l’utilisateur voit
seulement l’échec du bouton et aucun enregistrement n’est créé. La
reproduction locale renvoie :

```json
{"code":"consent_required","detail":"Le consentement de géolocalisation est requis avant l’émission."}
```

La contrainte d’un seul signal actif, le contrôle géographique, la limite de
tentatives et la protection de visibilité sont déjà centralisés dans le
service/les selectors et devront être conservés.

## 2. Notifications lues/non lues

### Flux observé

- `notifications.Notification` possède un `recipient` et un champ `read_at`.
- Les alertes destinées aux responsables sont dupliquées une fois par
  utilisateur dans `alerts/services.py::_notify_transport_admins`.
- Chaque copie possède même une clé d’événement comprenant l’identifiant du
  destinataire : `alert:<id>:admin:<user_id>:<suffix>`.
- `mark_notification_read` verrouille une seule notification et refuse toute
  action si son `recipient` n’est pas l’utilisateur courant.
- Les selectors et le context processor comptent les lignes non lues du seul
  utilisateur courant.

### Cause exacte

Le statut de lecture est actuellement conçu comme strictement individuel,
alors que le besoin métier du MVP demande un statut partagé pour un même
événement vu par les collègues d’un même périmètre. Lire la copie de
l’administrateur A ne modifie ni la copie de l’administrateur B ni celle d’un
chauffeur concerné. Le compteur de navigation reste donc non nul pour les
autres utilisateurs.

Le correctif devra introduire une identité de groupe/événement stable et
centraliser la lecture via le service, sans autoriser l’accès à des
notifications hors périmètre.

## 3. Dashboard et carte bloqués sur « Chargement… »

### Flux observé

- `templates/core/dashboard.html` charge Leaflet puis
  `static/js/dashboard_live.js`.
- Le script initialise la carte et appelle immédiatement
  `L.tileLayer(...)`.
- Ensuite seulement, `poll()` appelle `GET /dashboard/live/` et remplit les
  statistiques, trajets, alertes et incidents.
- `core/views.py::DashboardLiveView` renvoie le snapshot de
  `core/selectors.py::get_supervision_snapshot`.

### Cause exacte

Le fichier local `static/vendor/leaflet/leaflet.js` n’est pas Leaflet complet :
c’est une façade légère qui expose `map`, `marker` et `divIcon`, mais pas
`tileLayer`. L’appel à `L.tileLayer` provoque donc une
`TypeError: L.tileLayer is not a function` avant l’appel à `poll()`.

Comme le template conserve les éléments « Chargement… » jusqu’à ce que le
script rende le snapshot, l’exception laisse indéfiniment la carte et les
listes dans leur état initial. Le endpoint backend n’est pas la cause
principale : une requête authentifiée locale renvoie `200` avec les clés
`generated_at`, `statistics`, `buses`, `alerts`, `incidents` et `routes`.

La même dépendance à `L.tileLayer` est présente dans `signal_map.js` et touche
également les cartes de supervision/chauffeur. Les positions de bus absentes
du jeu de démonstration expliquent qu’aucun marqueur de bus ne soit affiché,
mais pas le blocage des listes.

## État de référence

- `manage.py check` : aucune erreur.
- Les tests ciblés des domaines concernés sont présents, mais la commande
  complète exécutée sur PostgreSQL termine avec 55 succès et 4 échecs
  préexistants dans les services d’alertes/inter-campus : PostgreSQL refuse
  `SELECT ... FOR UPDATE` avec `select_related` sur une relation nullable.
  Ces échecs sont indépendants des trois bugs analysés et seront surveillés
  pendant la validation.

