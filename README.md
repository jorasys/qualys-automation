# Qualys Automation v0.5

Outil CLI Python pour automatiser le téléchargement de scans et rapports depuis l'API Qualys.

## 🚀 Fonctionnalités

- ✅ Téléchargement de scans réseau (VM/PC) en CSV ou PDF
- ✅ Téléchargement de scans agent (host-based)
- ✅ Support de multiples formats CSV
- ✅ Gestion automatique des batches pour les rapports PDF
- ✅ Rate limiting et gestion des quotas API
- ✅ Logging complet des opérations
- ✅ Support de proxy
- ✅ Gestion robuste des erreurs avec retry automatique

## 📋 Prérequis

- Python 3.7+
- Compte Qualys avec accès API
- Connexion réseau (avec proxy optionnel)

## 🔧 Installation

1. **Cloner le repository**
```bash
git clone <repository-url>
cd qualys-automation-dev-v0.5
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configurer les credentials**
```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env avec vos credentials
nano .env
```

Remplir les informations suivantes dans `.env`:
```env
QUALYS_USERNAME=votre_username
QUALYS_PASSWORD=votre_password
```

4. **Configurer les paramètres** (optionnel)

Éditer `config/settings.json` pour ajuster:
- URL de l'API Qualys
- Configuration du proxy
- Paramètres de rate limiting
- Taille des batches pour les rapports
- Chemins de téléchargement

## 📖 Utilisation

### Scans Réseau en CSV

Télécharger des scans réseau au format CSV à partir d'un fichier de liste:

```bash
python main.py --scan-reseau scans.csv --csv
```

### Scans Réseau en PDF

Télécharger des scans réseau au format PDF:

```bash
python main.py --scan-reseau scans.csv --pdf
```

### Scans Agent

Télécharger les rapports agent (host-based):

```bash
python main.py --scan-agent
```

### Options Avancées

**Spécifier un dossier de sortie:**
```bash
python main.py --scan-reseau scans.csv --pdf --output-folder ./mes-rapports
```

**Aide:**
```bash
python main.py --help
```

## 📄 Format du Fichier CSV

Le fichier CSV peut avoir plusieurs formats:

### Format 1: Colonnes standard
```csv
id,title
scan/1234567890.12345,Mon Scan 1
scan/1234567890.12346,Mon Scan 2
```

### Format 2: Liste simple d'IDs
```csv
scan_id
scan/1234567890.12345
scan/1234567890.12346
```

### Format 3: Format générique (2+ colonnes)
```csv
scan_ref,scan_name
1234567890.12345,Mon Scan 1
1234567890.12346,Mon Scan 2
```

## 🏗️ Architecture

```
qualys-automation-dev-v0.5/
├── main.py                    # Point d'entrée CLI
├── .env                       # Credentials (non versionné)
├── .env.example              # Template de configuration
├── .gitignore                # Fichiers à ignorer
├── README.md                 # Cette documentation
├── config/
│   ├── settings.json         # Configuration système
│   └── templates.json        # Templates de rapports Qualys
├── src/
│   ├── api/
│   │   └── qualys_client.py  # Client API Qualys
│   ├── core/
│   │   ├── config.py         # Gestionnaire de configuration
│   │   └── exceptions.py     # Exceptions personnalisées
│   └── ui/
│       └── menu_manager.py   # Gestion des menus (optionnel)
├── data/
│   └── qualys_vuln.db        # Base de données SQLite
├── logs/
│   └── qualys_automation.log # Logs d'exécution
└── Downloads/                 # Dossier de téléchargement par défaut
```

## ⚙️ Configuration

### settings.json

Paramètres principaux dans `config/settings.json`:

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
    "download_path": "Downloads",
    "creation_controls": {
      "batch_size": 4,
      "max_wait_for_slots": 1800,
      "slot_check_interval": 30,
      "pause_between_reports": 2
    }
  },
  "logging": {
    "level": "INFO",
    "file": "logs/qualys_automation.log"
  }
}
```

### templates.json

Définit les templates de rapports Qualys à utiliser:

```json
{
  "scan_based_reports": [
    {
      "name": "Standard PDF Report",
      "template_id": "92297436",
      "output_format": "pdf"
    }
  ],
  "host_based_reports": [
    {
      "name": "PCI HostBased Report",
      "template_id": "92297434",
      "output_format": "pdf"
    }
  ]
}
```

## 📊 Logging

Les logs sont automatiquement créés dans `logs/qualys_automation.log` et incluent:

- Toutes les opérations API
- Erreurs et avertissements
- Progression des téléchargements
- Informations de rate limiting

Niveau de log configurable: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

## 🔒 Sécurité

⚠️ **IMPORTANT**: Ne jamais commiter le fichier `.env` contenant vos credentials!

Le fichier `.gitignore` est configuré pour exclure:
- `.env` (credentials)
- `logs/` (logs d'exécution)
- `Downloads/` (fichiers téléchargés)
- `*.db` (bases de données)

## 🐛 Dépannage

### Erreur de connexion API

```
❌ Erreur API Qualys: API connection failed
```

**Solutions:**
1. Vérifier les credentials dans `.env`
2. Vérifier la configuration du proxy
3. Vérifier la connectivité réseau
4. Consulter les logs: `logs/qualys_automation.log`

### Rate Limit Atteint

```
⚠️ ATTENTION: Seulement X requêtes API restantes!
```

**Solutions:**
1. Attendre la réinitialisation du quota (généralement 1 heure)
2. Réduire la taille des batches dans `settings.json`
3. Espacer les exécutions

### Timeout des Rapports

```
⚠️ Timeout atteint: X rapport(s) non terminé(s)
```

**Solutions:**
1. Augmenter `max_wait_for_slots` dans `settings.json`
2. Réduire `batch_size` pour moins de rapports simultanés
3. Vérifier l'état des rapports dans l'interface Qualys

## 📝 Exemples d'Utilisation

### Exemple 1: Téléchargement CSV Simple

```bash
# Créer un fichier scans.csv
echo "id,title" > scans.csv
echo "scan/1234567890.12345,Scan Production" >> scans.csv

# Télécharger
python main.py --scan-reseau scans.csv --csv
```

### Exemple 2: Rapports PDF avec Dossier Personnalisé

```bash
# Créer le dossier de sortie
mkdir -p ./rapports-mensuels

# Télécharger les rapports PDF
python main.py --scan-reseau scans.csv --pdf --output-folder ./rapports-mensuels
```

### Exemple 3: Scans Agent Automatiques

```bash
# Télécharger tous les rapports agent configurés
python main.py --scan-agent
```

## 🔄 Workflow Typique

1. **Préparer la liste des scans** dans un fichier CSV
2. **Lancer le téléchargement** avec la commande appropriée
3. **Surveiller la progression** dans la console
4. **Consulter les logs** en cas de problème
5. **Récupérer les fichiers** dans le dossier Downloads ou personnalisé

## 🤝 Contribution

Pour contribuer au projet:

1. Fork le repository
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changes (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📜 Licence

Ce projet est sous licence interne. Voir le fichier LICENSE pour plus de détails.

## 📞 Support

Pour toute question ou problème:
- Consulter les logs: `logs/qualys_automation.log`
- Vérifier la documentation Qualys API
- Contacter l'équipe de support

## 🔮 Roadmap

- [ ] Interface Web (Phase 3)
- [ ] Intégration Request Tracker (RT)
- [ ] Support de bases de données PostgreSQL
- [ ] Export vers d'autres formats
- [ ] Notifications par email
- [ ] Dashboard de monitoring

## 📚 Ressources

- [Documentation API Qualys](https://www.qualys.com/docs/qualys-api-vmpc-user-guide.pdf)
- [Python Requests Documentation](https://requests.readthedocs.io/)
- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)

---

**Version:** 0.5  
**Dernière mise à jour:** 2025-09-30