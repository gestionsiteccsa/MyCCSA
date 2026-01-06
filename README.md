# MyCCSA - Application Web Django

Application web métier développée avec Django, optimisée pour l'hébergement mutualisé o2switch.

## 🚀 Technologies

- **Backend** : Django 5.2+
- **Base de données** : PostgreSQL (production) / SQLite (développement)
- **Frontend** : Tailwind CSS 4.1 (production) + Vue.js 3
- **Hébergement** : o2switch (site mutualisé)
- **Performance** : Lighthouse 90+
- **Accessibilité** : WCAG AAA

## 📋 Prérequis

- Python 3.10+
- Node.js 18+ (pour Tailwind CSS)
- PostgreSQL (pour la production)
- pip
- npm (inclus avec Node.js)

## 🛠️ Installation

### 1. Cloner le projet

```bash
git clone <url-du-repo>
cd MyCCSA
```

### 2. Créer un environnement virtuel

```bash
python -m venv env
# Windows
env\Scripts\activate
# Linux/Mac
source env/bin/activate
```

### 3. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 4. Installer les dépendances Node.js (Tailwind CSS)

**Description** : Installe Tailwind CSS CLI et ses dépendances dans `node_modules/`. À faire une seule fois après le clonage du projet.

```bash
npm install
```

### 5. Créer le dossier logs

**Description** : Crée le dossier pour les fichiers de logs Django.

```bash
# Windows
mkdir logs

# Linux/Mac
mkdir -p logs
```

### 6. Configuration de l'environnement

**Description** : Configure les variables d'environnement nécessaires au projet.

Copier le fichier `.env.example` vers `.env` et modifier les valeurs :

```bash
cp .env.example .env
```

Éditer `.env` avec vos paramètres :
- `SECRET_KEY` : Générer une nouvelle clé secrète Django
- `DEBUG` : `True` pour développement, `False` pour production
- `ALLOWED_HOSTS` : Domaines autorisés (séparés par des virgules)
- Configuration PostgreSQL si nécessaire

### 7. Migrations de la base de données

**Description** : Applique les migrations de la base de données pour créer les tables nécessaires.

```bash
python manage.py migrate
```

### 8. Créer un superutilisateur

**Description** : Crée un compte administrateur pour accéder à l'interface d'administration Django.

```bash
python manage.py createsuperuser
```

### 9. Créer la table de cache

**Description** : Crée la table de cache en base de données (nécessaire pour le cache Django sur o2switch).

```bash
python manage.py createcachetable
```

### 10. Build Tailwind CSS (production)

**Description** : Compile et minifie le CSS Tailwind pour la production. Génère `static/css/output.css` qui sera commité dans Git.

```bash
npm run build
```

### 11. Collecter les fichiers statiques (production)

**Description** : Collecte tous les fichiers statiques (CSS, JS, images) dans le dossier `staticfiles/` pour la production.

```bash
python manage.py collectstatic --noinput
```

### 12. Lancer le serveur de développement

**Description** : Démarre le serveur de développement Django.

```bash
python manage.py runserver
```

Le site sera accessible sur `http://127.0.0.1:8000/`

## 🔄 Workflow de développement

### Mode développement (watch automatique)

**Description** : Lance Tailwind CSS en mode watch. Le CSS sera recompilé automatiquement à chaque modification de vos templates HTML. Laissez cette commande tourner pendant le développement.

```bash
npm run watch
```

**Note** : Ouvrez un terminal séparé pour cette commande et laissez-le ouvert pendant que vous développez.

### Build avant commit

**Description** : Avant de commiter vos modifications, arrêtez le mode watch (Ctrl+C) et lancez cette commande pour générer le CSS de production minifié.

```bash
npm run build
```

Ensuite, commitez le fichier `static/css/output.css` :

```bash
git add static/css/output.css
git commit -m "Mise à jour CSS Tailwind"
git push
```

## 📁 Structure du projet

```
MyCCSA/
├── app/                    # Configuration principale Django
│   ├── settings.py        # Paramètres du projet
│   ├── urls.py            # URLs principales
│   └── wsgi.py            # Configuration WSGI
├── home/                   # Application principale
│   ├── models.py          # Modèles de données
│   ├── views.py           # Vues
│   ├── urls.py            # URLs de l'app
│   └── templates/         # Templates de l'app
├── templates/              # Templates globaux
│   └── base.html          # Template de base
├── src/                    # Sources CSS
│   └── css/
│       └── input.css      # Fichier source Tailwind CSS
├── static/                 # Fichiers statiques (dev)
│   └── css/
│       └── output.css    # CSS Tailwind compilé
├── staticfiles/           # Fichiers statiques collectés (production)
├── media/                 # Fichiers médias uploadés
├── logs/                  # Fichiers de logs
├── .env                   # Variables d'environnement (non versionné)
├── .env.example          # Exemple de configuration
├── .gitignore            # Fichiers ignorés par Git
├── .flake8               # Configuration Flake8
├── package.json          # Configuration npm (Tailwind CSS)
├── tailwind.config.js    # Configuration Tailwind CSS
├── requirements.txt       # Dépendances Python
└── README.md             # Ce fichier
```

## 🔒 Sécurité

- **SECRET_KEY** : Ne jamais commiter la clé secrète. Utiliser les variables d'environnement.
- **DEBUG** : Toujours `False` en production.
- **ALLOWED_HOSTS** : Configurer les domaines autorisés en production.
- Les fichiers sensibles sont exclus via `.gitignore`.

## 🧪 Tests

```bash
python manage.py test
```

Avec couverture de code :

```bash
coverage run --source='.' manage.py test
coverage report
```

## 📝 Qualité de code

Vérifier le code avec Flake8 :

```bash
flake8 .
```

## 🚀 Déploiement sur o2switch

**Important** : Le CSS Tailwind est compilé en local et commité dans Git. Pas besoin de Node.js/npm sur le serveur !

### Commandes à exécuter sur le serveur o2switch

1. **Configurer les variables d'environnement**
   - Description : Configurer les variables d'environnement sur le serveur (SECRET_KEY, DEBUG, ALLOWED_HOSTS, etc.)
   - Action : Créer/modifier le fichier `.env` sur le serveur

2. **Configurer PostgreSQL**
   - Description : Configurer la connexion à la base de données PostgreSQL sur o2switch
   - Action : Configurer les variables DB_NAME, DB_USER, DB_PASSWORD dans `.env`

3. **Récupérer le code**
   - Description : Récupérer le code depuis Git (inclut le CSS compilé)
   ```bash
   git pull
   ```

4. **Exécuter les migrations**
   - Description : Appliquer les migrations de la base de données
   ```bash
   python manage.py migrate
   ```

5. **Créer la table de cache**
   - Description : Créer la table de cache en base de données (nécessaire pour le cache Django)
   ```bash
   python manage.py createcachetable
   ```

6. **Créer le dossier logs**
   - Description : Créer le dossier pour les fichiers de logs (si nécessaire)
   ```bash
   mkdir -p logs
   ```

7. **Collecter les fichiers statiques**
   - Description : Collecte tous les fichiers statiques (inclut le CSS Tailwind déjà compilé) dans `staticfiles/` pour la production
   ```bash
   python manage.py collectstatic --noinput
   ```

8. **Configurer le serveur web**
   - Description : Configurer le serveur web (Apache/Nginx) pour servir `/media/` et `/static/`
   - Action : Configuration serveur web (généralement déjà fait par o2switch)

**Note** : Le fichier `static/css/output.css` est déjà compilé et présent dans le code Git. Pas besoin de `npm install` ni `npm run build` sur le serveur !

## 📚 Documentation

- [Documentation Django](https://docs.djangoproject.com/)
- [Règles du projet (.cursorrules)](.cursorrules)

## 👥 Contribution

1. Créer une branche pour votre fonctionnalité
2. Faire vos modifications
3. Vérifier avec Flake8 : `flake8 .`
4. Exécuter les tests : `python manage.py test`
5. Créer une pull request

## 📄 Licence

[À définir]

## 🔗 Liens utiles

- [Tailwind CSS 4.1](https://tailwindcss.com/)
- [Vue.js 3](https://vuejs.org/)
- [o2switch](https://www.o2switch.fr/)


