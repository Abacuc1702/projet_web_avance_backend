**Dépendances**

Vous Trouverez dans le fichier "requirements.txt" toutes les dépendances nécessaires pour pouvoir lancer le projet.

Pour installer les dépendances:

* Naviguer (dans votre terminal) jusque dans le dossier qui contient le fichier en question.
* taper la commande suivante: `pip install -r requirements.txt`

NB: Assurez-vous d'avoir python installé sur votre machine

**Execution du projet**

Pour executer le projet, vous devez d'abord démarrer le serveur

* Assurez vous d'être dans le repertoire du projet et saisissez la commande suivante :

`python manage.py runserver`

* ensuite ouvrez le navigateur et saisissez l'addresse du serveur (par défaut 127.0.0.1:8000)
* puis saisissez l'addresse à laquelle vous voulez acceder

pour l'utilisation hors de votre pc où par une application tierce:

* lancez le serveur sur l'adresse 0.0.0.0:800 avec cette commande: `python manage.py runserver 0.0.0.0:8000`
* l'adresse IP de votre machine sera maintenant l'adresse du serveur
