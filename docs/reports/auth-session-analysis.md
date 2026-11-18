# Analyse de l’authentification et des sessions

## Périmètre examiné

L’audit couvre `config/settings/base.py`, `config/settings/production.py`, `config/urls.py`, le module `estuairefleet/users` (modèle, backend, formulaires, vues, permissions, middleware, services, sélecteurs et tests) ainsi que les vues Web qui utilisent les protections d’authentification.

## Flux constaté

- La connexion utilise `IdentifierLoginView`, sous-classe de Django `LoginView`. Le backend `IdentifierBackend` recherche un utilisateur par e-mail ou matricule et vérifie son mot de passe.
- Le premier POST valide les identifiants, crée un défi OTP et conserve son identifiant et le `next` dans la session. L’utilisateur n’est pas encore connecté à ce stade.
- `OTPVerifyView` valide le code, appelle `django.contrib.auth.login()`, inscrit `otp_verified_at` dans la session puis redirige vers le `next` validé, ou vers `core:home`.
- L’inscription publique suit la même étape OTP. Après création du profil, elle connecte l’utilisateur puis redirige vers `core:home`.
- `core:home` distribue les utilisateurs selon leur rôle : étudiant vers `signals:home`, chauffeur vers `signals:driver_map`, personnel vers `signals:monitor`, administrateur vers `core:dashboard`.
- La déconnexion est une `LogoutView` avec confirmation et `next_page="core:home"`. Django vide la session lors de la déconnexion.

## Sessions et ordre des middlewares

Le middleware de session est installé avant `AuthenticationMiddleware`, dans l’ordre requis. L’application `django.contrib.sessions` est installée. Le moteur de session n’est pas remplacé : Django utilise son backend de base de données. `SESSION_COOKIE_HTTPONLY=True` est configuré ; les options de durée, nom de cookie, `SameSite`, domaine et moteur conservent les valeurs par défaut de Django. En production seulement, les cookies de session et CSRF sont `Secure` et le site force HTTPS. Cette séparation est adaptée au développement HTTP local.

Aucun réglage explicite observé ne supprime la session lors de la navigation. `login()` remplace la clé de session au besoin tout en conservant les données de session non liées à l’authentification. Le scénario décrit comme « session perdue » correspond donc principalement au contrôle OTP décrit ci-dessous, et non à une preuve de perte du cookie ou du stockage de session. Ce diagnostic devra être confirmé par les tests du parcours.

## Causes et défauts précis

1. **Expiration OTP présentée comme une déconnexion.** `ESTUAIREFLEET_OTP_SESSION_AGE_SECONDS` vaut 3 600 secondes. `OTPRequiredMixin` redirige un utilisateur toujours authentifié vers `users:login` lorsque `otp_verified_at` est absent, invalide ou trop ancien. La session Django reste authentifiée ; seul le contrôle OTP applicatif est expiré. La page de login n’a pas de comportement dédié pour un utilisateur déjà authentifié, ce qui rend cette réauthentification déroutante.
2. **Reprise de navigation après expiration perdue.** Le mixin écrit `otp_reauth_next` dans la session avant la redirection, mais aucun code ne le lit. `IdentifierLoginView.form_valid()` ne conserve que `POST[next]`. Après expiration OTP, le navigateur reçoit une redirection login sans `next`; après le nouvel OTP, `_safe_next_url()` renvoie donc vers `core:home` au lieu de la page initialement demandée.
3. **Comportement `next` non unifié.** Les mixins Django passent `next` à la page login. Les chemins personnalisés appellent parfois `redirect("users:login")` directement, sans préserver le chemin. Le contrôle d’hôte de `_safe_next_url()` protège déjà contre une redirection externe, mais sa valeur de repli est codée en dur.
4. **Protection inégale.** Les vues métier utilisent les mixins à rôles, qui exigent aussi une OTP fraîche. D’autres vues utilisent uniquement `LoginRequiredMixin` (par exemple le réseau de flotte), qui n’impose pas la vérification OTP. `UserDetailView` et `UserRedirectView` répètent également un contrôle d’authentification manuel après le mixin.
5. **Redirections après inscription et rôle.** L’inscription renvoie systématiquement vers `core:home`, qui distribue correctement les rôles connus. La connexion OTP respecte `next`, sinon utilise `core:home`. Le réglage global `LOGIN_REDIRECT_URL` est également `core:home`, mais le flux personnalisé ne délègue pas à Django pour décider de sa destination.
6. **Déconnexion.** La redirection par défaut est explicitement fournie à `LogoutView`; le template de confirmation et les méthodes HTTP autorisées sont personnalisés. Aucun autre réglage `LOGOUT_REDIRECT_URL` n’est défini. Les tests existants ne couvrent pas la déconnexion, l’expiration OTP, la reprise de `next` ni les destinations propres à chaque rôle.

## Conclusion de l’étape 1

La cause reproduisible la plus directe est l’expiration de la fenêtre OTP d’une heure : l’utilisateur conserve sa session Django, mais certaines pages exigent de nouveau l’OTP et le renvoient vers le formulaire de connexion. Le chemin demandé est ensuite perdu car `otp_reauth_next` n’est jamais consommé. Aucun défaut évident d’ordre de middleware ou de persistance de session n’a été trouvé. Les étapes de correction doivent distinguer la session d’authentification Django de l’ancienneté de la vérification OTP, harmoniser la protection des vues et conserver un `next` local sûr à travers les deux facteurs.

## Vérifications à effectuer dans les étapes suivantes

- Définir explicitement les paramètres de session compatibles avec HTTP local et HTTPS en production, sans rendre le cookie local inaccessible.
- Tester login et inscription avec OTP, navigation vers une URL protégée, expiration OTP et reprise vers la destination demandée.
- Confirmer l’accès protégé pour étudiant, chauffeur, administrateur et personnel ; confirmer le refus après déconnexion.
- Vérifier que `next` ne permet jamais une redirection vers un hôte externe et qu’un utilisateur déjà connecté ne reste pas bloqué sur l’écran de connexion.
