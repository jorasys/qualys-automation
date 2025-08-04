# Qualys Automation - Version 0.3

Un script Python refactorisé utilisant l'API Qualys pour la génération automatisée de rapports avec base de données SQLite et architecture modulaire.

## 🚀 Nouveautés Version 0.3

### Architecture Refactorisée
- **Configuration externalisée** : Plus de credentials hardcodés
- **Base de données SQLite** : Persistance des données avec SQLAlchemy
- **Architecture modulaire** : Séparation claire des responsabilités
- **Gestion d'erreurs améliorée** : Exceptions personnalisées et retry logic
- **Interface utilisateur améliorée** : Support inquirer avec fallback texte

### Structure du Projet
```
qualys-automation/
├── src/
│   ├── core/           # Configuration, DB, exceptions
│   ├── api/            # Client Qualys refactorisé
│   ├── models/         # Modèles SQLAlchemy
│   ├── services/       # Logique métier
│   ├── repositories/   # Accès aux données
│   └── ui/             # Interface utilisateur
├── config/             # Fichiers de configuration
├── scripts/            # Scripts d'initialisation
├── data/               # Base de données SQLite
├── logs/               # Fichiers de logs
└── main_v03.py         # Point d'entrée v0.3
```

## 📋 Prérequis

- Python 3.8+
- Accès à l'API Qualys
- Proxy configuré (si nécessaire)

## 🛠️ Installation

### 1. Cloner le projet
```bash
git clone <repository-url>
cd qualys-automation
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 3. Configuration

#### Copier le fichier d'environnement
```bash
copy .env.example .env
```

#### Éditer le fichier `.env`
```env
QUALYS_USERNAME=votre_nom_utilisateur
QUALYS_PASSWORD=votre_mot_de_passe
ENVIRONMENT=development
DEBUG=true
```

#### Vérifier les configurations
Les fichiers de configuration sont dans le dossier `config/` :
- `settings.json` : Configuration générale
- `templates.json` : Templates de rapports

### 4. Initialiser la base de données
```bash
python scripts/init_db.py init
```

### 5. (Optionnel) Migrer les données existantes
Si vous avez des fichiers JSON de l'ancienne version :
```bash
python scripts/migrate_existing_data.py migrate
```

## 🚀 Utilisation

### Lancement du script principal
```bash
python main_v03.py
```

### Scripts utilitaires

#### Gestion de la base de données
```bash
# Initialiser la base de données
python scripts/init_db.py init

# Réinitialiser la base de données (supprime toutes les données)
python scripts/init_db.py reset

# Afficher les informations de la base de données
python scripts/init_db.py info
```

#### Migration des données
```bash
# Migrer les données JSON existantes
python scripts/migrate_existing_data.py migrate

# Afficher le statut de la migration
python scripts/migrate_existing_data.py status
```

## 📊 Fonctionnalités

### Workflow Principal
1. **Récupération des scans** depuis l'API Qualys
2. **Sélection interactive** des scans et templates
3. **Génération automatique** des rapports (PDF/CSV)
4. **Surveillance** du statut des rapports
5. **Téléchargement automatique** des rapports prêts

### Types de Rapports Supportés
- **Scan-based** : Rapports basés sur des scans spécifiques
- **Host-based** : Rapports basés sur des templates PCI
- **Formats** : PDF et CSV

### Interface Utilisateur
- **Interface graphique** avec `inquirer` (si disponible)
- **Interface texte** en fallback
- **Sélection multiple** avec cases à cocher
- **Navigation intuitive** avec raccourcis clavier

## 🗄️ Base de Données

### Modèles de Données
- **Vulnerabilities** : Vulnérabilités Qualys
- **Assets** : Assets scannés
- **VulnerabilityInstances** : Instances de vulnérabilités sur des assets
- **ScanReports** : Rapports générés
- **SyncLog** : Logs des opérations

### Requêtes Disponibles
- Statistiques des vulnérabilités par sévérité
- Historique des rapports générés
- Logs des synchronisations

## ⚙️ Configuration

### Fichier `config/settings.json`
```json
{
  "api": {
    "base_url": "qualysapi.qualys.eu",
    "timeout": 30,
    "max_retries": 3,
    "proxy": {
      "enabled": true,
      "url": "http://127.0.0.1:3128"
    }
  },
  "reports": {
    "max_concurrent": 8,
    "download_path": "~/Downloads",
    "formats": ["pdf", "csv"]
  }
}
```

### Fichier `config/templates.json`
Configuration des templates de rapports Qualys avec IDs et formats.

## 🔧 Développement

### Structure des Modules
- **`src/core/`** : Configuration, base de données, exceptions
- **`src/api/`** : Client API Qualys avec retry logic
- **`src/models/`** : Modèles SQLAlchemy
- **`src/services/`** : Logique métier (rapports, etc.)
- **`src/repositories/`** : Accès aux données avec patterns Repository
- **`src/ui/`** : Interface utilisateur modulaire

### Tests
```bash
# Lancer les tests (si configurés)
pytest tests/
```

## 📝 Logs

Les logs sont stockés dans `logs/qualys_automation.log` avec rotation automatique.

## 🔒 Sécurité

- ✅ **Credentials externalisés** dans `.env`
- ✅ **Fichier `.env` dans `.gitignore`**
- ✅ **Gestion sécurisée des sessions API**
- ✅ **Validation des entrées utilisateur**

## 🚧 Roadmap

### Phase 2 (Prochaine)
- Interface web avec FastAPI
- API REST pour intégration
- Dashboard de visualisation

### Phase 3
- Intégration Request Tracker
- Synchronisation bidirectionnelle
- Gestion des tickets de vulnérabilités

### Phase 4
- Fonctionnalités avancées
- Reporting automatisé
- Optimisations performance

## 🐛 Dépannage

### Erreurs Communes

#### "Missing Qualys credentials"
- Vérifiez que le fichier `.env` existe
- Vérifiez que `QUALYS_USERNAME` et `QUALYS_PASSWORD` sont définis

#### "Database not initialized"
- Lancez `python scripts/init_db.py init`

#### "Connection timeout"
- Vérifiez la configuration du proxy
- Vérifiez la connectivité réseau

### Support
Pour les problèmes, consultez les logs dans `logs/qualys_automation.log`.

## 📄 Licence

[Votre licence ici]

## 🤝 Contribution

[Instructions de contribution ici]