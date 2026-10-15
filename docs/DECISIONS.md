# Décisions et hypothèses

Date initiale : 14 octobre 2026; audit de reprise : 16 octobre 2026

1. Les deux cahiers de référence annoncés ne sont pas présents dans le dépôt. Les exigences détaillées dans la mission utilisateur sont retenues comme spécification fonctionnelle et comme représentation normative des états UML.
2. `Incident` est rattaché à l’application `fleet`, car il décrit l’état opérationnel d’un bus ou d’un trajet et doit être administrable avec la flotte.
3. Les identifiants UUID et `BaseModel` existants sont conservés pour les entités sensibles ; les noms de champs existants sont préservés lorsqu’ils ne contredisent pas la confidentialité ou les états métier.
4. Le polling JSON reste le mécanisme temps réel du MVP. Les réponses utilisent un paramètre `since` et ne révèlent jamais la position d’un étudiant à un autre étudiant.
5. Les données de position sont traitées comme temporaires : elles sont effacées ou anonymisées par une tâche périodique après la durée configurée.
6. Le fournisseur de messages courts reste une interface abstraite avec un backend console local ; aucun fournisseur externe n’est nécessaire pour le MVP.
7. Les exports administratifs sont limités aux indicateurs opérationnels de transport et ne contiennent aucune donnée commerciale.
8. Le répertoire `staticfiles/` est un artefact de collecte et n’est pas une source frontend. Le pipeline unique reste npm + Tailwind + Flowbite.
9. Le `.venv` existant appartient à `root` et ne peut pas être réparé sans modifier des fichiers hors périmètre. Les contrôles utilisent donc un environnement uv séparé sous `/tmp`.
10. Les cahiers de charge et UML annoncés restent absents du dépôt; les exigences de la mission utilisateur et les statuts déjà codés constituent le contrat de reprise. Toute divergence corrigée est reportée dans le rapport final.
11. La réponse chauffeur « J'arrive » termine l'alerte lorsqu'elle est en cours; l'ancien test qui attendait encore `EnCours` est considéré obsolète au regard de la machine d'états demandée.
