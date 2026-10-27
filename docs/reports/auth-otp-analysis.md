# Analyse initiale de l’authentification et des OTP

## Périmètre

Analyse réalisée sur le domaine `estuairefleet.users`, ses migrations, services,
sélecteurs, formulaires, vues, routes, templates, réglages et tests associés.

## État du dépôt au démarrage

Le dépôt était propre avant l’analyse. Le socle d’authentification existe déjà
et couvre une connexion par e-mail ou matricule, une validation OTP de connexion
et une validation OTP d’inscription.

Le flux de réinitialisation présent est encore le flux natif Django par lien
signé. Il ne constitue donc pas le flux OTP demandé.

## Fonctionnement actuel

### Connexion

- `IdentifierBackend` recherche l’utilisateur par e-mail ou matricule et vérifie
  le mot de passe.
- `IdentifierLoginView` ne crée pas de session authentifiée immédiatement.
- Si l’utilisateur possède une adresse e-mail, un challenge de type `login` est
  créé puis l’identifiant utilisateur et le challenge sont conservés en session.
- `OTPVerifyView` valide le code avant d’appeler `login()` et renseigne
  `otp_verified_at`.
- La redirection `next` est contrôlée par `_safe_next_url`.

### Inscription

- `StudentSignupView` conserve les données d’inscription et un hash du mot de
  passe dans la session.
- Un challenge de type `signup` est envoyé avant la création du compte.
- Le compte et son profil sont créés uniquement après validation du code.
- La session est ensuite authentifiée et marquée comme validée par OTP.

### Modèle OTP

`OTPChallenge` est un `BaseModel` à clé UUID contenant :

- l’adresse e-mail ;
- l’usage (`login` ou `signup`) ;
- le hash du code ;
- la date d’expiration ;
- le nombre de tentatives ;
- la date de consommation.

Le code est généré avec `secrets`, stocké haché, valide dix minutes par défaut,
et consommé dans une transaction avec verrouillage de ligne. Le nombre maximal
de tentatives est fixé à cinq.

### Services

- `issue_otp()` invalide les challenges actifs du même e-mail et du même usage,
  génère un code à six chiffres et l’envoie de façon synchrone par e-mail.
- `verify_otp()` utilise `select_for_update()`, vérifie l’expiration, limite les
  tentatives, puis consomme le challenge en cas de succès.
- `send_otp_email()` est directement couplé à `django.core.mail.send_mail`.
- Le paramètre `user` de `issue_otp()` est accepté mais n’est pas utilisé ni
  enregistré dans `OTPChallenge`.

## Routes et interfaces présentes

### Routes du domaine users

- `/users/login/` : connexion par matricule ou e-mail ;
- `/users/otp/` : validation et renvoi du challenge courant ;
- `/users/signup/` : inscription publique ;
- `/users/password/reset/` : `django.contrib.auth.views.PasswordResetView` ;
- `/users/password/reset/done/` ;
- `/users/password/reset/<uidb64>/<token>/` ;
- `/users/password/reset/complete/`.

Le projet expose aussi les routes de réinitialisation d’allauth sous
`/accounts/password/reset/`, avec un second mécanisme indépendant.

### Templates

- `account/login.html` ne contient pas de lien vers « Mot de passe oublié ? » ;
- `account/otp_verify.html` contient un formulaire de renvoi partagé par la
  connexion et l’inscription ;
- `users/password_reset.html` décrit l’envoi d’un lien, pas l’envoi d’un OTP ;
- les pages de confirmation correspondent au flux natif par lien.

## Options de renvoi d’OTP recensées

Une seule option de renvoi est visible : le bouton de
`account/otp_verify.html`, envoyé en POST vers la même vue `users:otp_verify`
avec le champ `resend`.

La vue détermine l’usage depuis la session :

- connexion : elle retrouve l’utilisateur via `login_user_id` ;
- inscription : elle retrouve l’adresse dans `pending_signup`.

Il n’existe pas encore de renvoi dédié à la réinitialisation du mot de passe.

## Bugs, risques et manques identifiés

1. `OTPPurpose` ne prévoit pas d’usage pour la réinitialisation du mot de passe.
2. Le flux `/users/password/reset/` est par lien signé et ne passe ni par
   `OTPChallenge`, ni par `verify_otp()`.
3. Le template e-mail standard attendu par `PasswordResetView`,
   `registration/password_reset_email.html`, n’est pas présent dans le dépôt.
   L’envoi du formulaire natif risque donc d’échouer au rendu du message.
4. La page de connexion ne donne aucun accès au parcours de récupération.
5. Le renvoi OTP n’a aucun délai minimal, aucun compteur de renvois et aucune
   limitation par session, adresse ou adresse réseau : les envois peuvent être
   répétés sans borne.
6. Chaque renvoi invalide l’ancien challenge, mais aucun mécanisme de cooldown
   n’empêche l’émission immédiate d’un nouveau code.
7. `issue_otp()` n’applique pas de limitation même lorsqu’il est appelé hors de
   la vue de validation.
8. La structure actuelle est uniquement e-mail ; aucun adaptateur d’envoi
   distinct ne prépare explicitement un second canal.
9. Les sessions OTP sont fonctionnelles pour les parcours existants, mais le
   stockage du challenge n’est pas lié à un utilisateur et dépend de plusieurs
   clés de session (`login_user_id`, `pending_signup`, `pending_otp`).
10. La couverture de tests ne contient aucun scénario de réinitialisation,
    d’expiration, de consommation unique, de limitation de tentatives ou de
    renvoi temporisé.
11. L’image Docker locale ne contient pas les dépendances de développement :
    `manage.py test estuairefleet.users` trouve six tests mais échoue à
    importer `test_users.py` avec `ModuleNotFoundError: No module named
    'pytest'`.

## Constats de validation

- `manage.py check` : aucun problème Django détecté.
- L’inventaire des routes confirme la coexistence du flux `users` natif et du
  flux allauth sous `accounts`.
- Les tests existants de connexion et d’inscription couvrent la validation OTP
  de base, mais pas les cas listés ci-dessus.

## Conclusion de l’étape 1

Le projet dispose d’un socle OTP réutilisable pour la connexion et l’inscription,
avec hachage, expiration, verrouillage et consommation unique. Le parcours
« Mot de passe oublié » reste toutefois un scaffold Django par lien, sans
intégration au modèle OTP, sans interface depuis la connexion et sans protection
de renvoi. L’étape suivante doit étendre le modèle d’usage OTP et les services
avant de brancher les vues et les routes.
