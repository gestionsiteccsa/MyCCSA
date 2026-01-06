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

```bash
npm install
```

### 5. Créer le dossier logs

```bash
# Windows
mkdir logs

# Linux/Mac
mkdir -p logs
```

### 6. Configuration de l'environnement

Copier le fichier `.env.example` vers `.env` et modifier les valeurs :

```bash
cp .env.example .env
```

Éditer `.env` avec vos paramètres :
- `SECRET_KEY` : Générer une nouvelle clé secrète Django
- `DEBUG` : `True` pour développement, `False` pour production
- `ALLOWED_HOSTS` : Domaines autorisés (séparés par des virgules)
- Configuration PostgreSQL si nécessaire

### 7. Build Tailwind CSS

```bash
# Build de production (minifié)
npm run build

# Ou en mode watch pour le développement
npm run watch
```

### 8. Migrations de la base de données

```bash
python manage.py migrate
```

### 9. Créer un superutilisateur

```bash
python manage.py createsuperuser
```

### 10. Créer la table de cache

```bash
python manage.py createcachetable
```

### 11. Collecter les fichiers statiques (production)

```bash
python manage.py collectstatic --noinput
```

### 12. Lancer le serveur de développement

```bash
python manage.py runserver
```

Le site sera accessible sur `http://127.0.0.1:8000/`

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

1. Configurer les variables d'environnement sur le serveur
2. Configurer PostgreSQL sur o2switch
3. Installer les dépendances Node.js : `npm install`
4. Build Tailwind CSS : `npm run build`
5. Exécuter les migrations : `python manage.py migrate`
6. Créer la table de cache : `python manage.py createcachetable`
7. Créer le dossier logs : `mkdir logs` (si nécessaire)
8. Collecter les fichiers statiques : `python manage.py collectstatic --noinput`
9. Configurer le serveur web pour servir `/media/` et `/static/`

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


